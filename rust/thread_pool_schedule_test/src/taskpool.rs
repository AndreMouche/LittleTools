// #![crate_type = "lib"]
// #![feature(fnbox)]
// extern crate ordermap;
use ordermap::OrderMap as HashMap;
use std::usize;
use std::sync::{Arc, Mutex, Condvar};
use std::sync::mpsc::{Sender, Receiver, channel};
use std::thread::{Builder, JoinHandle};
use std::boxed::FnBox;
use std::collections::{BinaryHeap, VecDeque};
use std::cmp::Ordering;
use std::sync::atomic::{AtomicUsize, Ordering as AtomicOrdering};
use std::hash::Hash;
use std::marker::PhantomData;
use std::fmt::{self, Write, Debug, Formatter};

pub struct Task<T> {
    // The task's id in the pool. Each task has a unique id,
    // and it's always bigger than preceding ones.
    id: u64,

    // which group the task belongs to.
    gid: T,
    task: Box<FnBox() + Send>,
}

impl<T: Debug> Debug for Task<T> {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        write!(f, "task_id:{},group_id:{:?}", self.id, self.gid)
    }
}

impl<T> Task<T> {
    fn new<F>(id: u64, gid: T, job: F) -> Task<T>
        where F: FnOnce() + Send + 'static
    {
        Task {
            id: id,
            gid: gid,
            task: Box::new(job),
        }
    }
}

impl<T> Ord for Task<T> {
    fn cmp(&self, right: &Task<T>) -> Ordering {
        self.id.cmp(&right.id).reverse()
    }
}

impl<T> PartialEq for Task<T> {
    fn eq(&self, right: &Task<T>) -> bool {
        self.cmp(right) == Ordering::Equal
    }
}

impl<T> Eq for Task<T> {}

impl<T> PartialOrd for Task<T> {
    fn partial_cmp(&self, rhs: &Task<T>) -> Option<Ordering> {
        Some(self.cmp(rhs))
    }
}

pub trait ScheduleQueue<T: Debug> {
    fn pop(&mut self) -> Option<Task<T>>;
    fn push(&mut self, task: Task<T>);
    fn on_task_finished(&mut self, gid: &T);
    fn on_task_started(&mut self, gid: &T);
}

#[derive(Debug)]
pub struct ReachConcurrencyLimit<T: Debug>(pub T);

struct GroupStatisticsItem {
    running_count: usize,
    high_priority_queue_count: usize,
    low_priority_queue_count: usize,
}

impl GroupStatisticsItem {
    fn new() -> GroupStatisticsItem {
        GroupStatisticsItem {
            running_count: 0,
            high_priority_queue_count: 0,
            low_priority_queue_count: 0,
        }
    }

    fn sum(&self) -> usize {
        self.running_count + self.high_priority_queue_count + self.low_priority_queue_count
    }
}

pub struct FIFOQueue<T> {
    tasks: VecDeque<Task<T>>,
}

impl<T: Hash + Eq + Ord + Send + Clone + Debug> FIFOQueue<T> {
    pub fn new() -> FIFOQueue<T> {
        FIFOQueue { tasks: VecDeque::new() }
    }
}

impl<T: Hash + Eq + Ord + Send + Clone + Debug> ScheduleQueue<T> for FIFOQueue<T> {
    fn push(&mut self, task: Task<T>) {
        self.tasks.push_back(task);
    }
    fn pop(&mut self) -> Option<Task<T>> {
        self.tasks.pop_front()
    }
    fn on_task_finished(&mut self, _: &T) {}
    fn on_task_started(&mut self, _: &T) {}
}

pub struct SpeedupSmallGroups<T> {
    high_priority_queue: VecDeque<Task<T>>,
    low_priority_queue: VecDeque<Task<T>>,
    big_group_currency_on_busy: usize,
    statistics: HashMap<T, GroupStatisticsItem>,
}


impl<T: Hash + Eq + Ord + Send + Clone + Debug> SpeedupSmallGroups<T> {
    pub fn new(group_concurrency_on_busy: usize) -> SpeedupSmallGroups<T> {
        SpeedupSmallGroups {
            high_priority_queue: VecDeque::new(),
            low_priority_queue: VecDeque::new(),
            statistics: HashMap::new(),
            big_group_currency_on_busy: group_concurrency_on_busy,
        }
    }

    fn pop_from_high_priority_queue(&mut self) -> Option<Task<T>> {
        if self.high_priority_queue.is_empty() {
            return None;
        }
        let task = self.high_priority_queue.pop_front().unwrap();
        let mut statistics = self.statistics.get_mut(&task.gid).unwrap();
        statistics.high_priority_queue_count -= 1;
        Some(task)
    }

    fn pop_from_low_priority_queue(&mut self) -> Option<Task<T>> {
        if self.low_priority_queue.is_empty() {
            return None;
        }
        let task = self.low_priority_queue.pop_front().unwrap();
        let mut statistics = self.statistics
            .get_mut(&task.gid)
            .unwrap();
        statistics.low_priority_queue_count -= 1;
        Some(task)
    }
}

impl<T: Hash + Eq + Ord + Send + Clone + Debug> ScheduleQueue<T> for SpeedupSmallGroups<T> {
    fn push(&mut self, task: Task<T>) {
        let mut statistics = self.statistics
            .entry(task.gid.clone())
            .or_insert(GroupStatisticsItem::new());
        if statistics.sum() == 0 {
            self.high_priority_queue.push_back(task);
            statistics.high_priority_queue_count += 1;
        } else {
            self.low_priority_queue.push_back(task);
            statistics.low_priority_queue_count += 1;
        }
    }

    fn pop(&mut self) -> Option<Task<T>> {
        if self.low_priority_queue.is_empty() {
            return self.pop_from_high_priority_queue();
        }

        if self.high_priority_queue.is_empty() {
            return self.pop_from_low_priority_queue();
        }

        let pop_from_waiting1 = {
            let t1 = self.high_priority_queue.front().unwrap();
            let t2 = self.low_priority_queue.front().unwrap();
            t1.id < t2.id ||
            (self.statistics[&t2.gid].running_count >= self.big_group_currency_on_busy)
        };

        if !pop_from_waiting1 {
            return self.pop_from_low_priority_queue();
        }
        self.pop_from_high_priority_queue()
    }

    fn on_task_started(&mut self, gid: &T) {
        let mut statistics = self.statistics.get_mut(gid).unwrap();
        statistics.running_count += 1;
    }

    fn on_task_finished(&mut self, gid: &T) {
        let count = {
            let mut statistics = self.statistics.get_mut(gid).unwrap();
            statistics.running_count -= 1;
            statistics.sum()
        };
        if count == 0 {
            self.statistics.remove(gid);
        }
    }
}

// `BigGroupThrottledQueue` tries to throttle group's concurrency to
//  `group_concurrency_limit` when all threads are busy.
// When one worker asks a task to run, it schedules in the following way:
// 1. Find out which group has a running number that is smaller than
//    that of `group_concurrency_limit`.
// 2. If more than one group meets the first point, run the one who
//    comes first.
// If no group meets the first point, choose according to the following rules:
// 1. Select the groups with least running tasks.
// 2. If more than one group meets the first point,choose the one
//     whose task comes first(with the minimum task's ID)
pub struct BigGroupThrottledQueue<T> {
    // The Tasks in `high_priority_queue` have higher priority than
    // tasks in `low_priority_queue`.
    high_priority_queue: BinaryHeap<Task<T>>,

    // gid => tasks array. If `group_statistics[gid]` is bigger than
    // `group_concurrency_limit`(which means the number of on-going tasks is
    // more than `group_concurrency_limit`), the rest of the group's tasks
    // would be pushed into `low_priority_queue[gid]`
    low_priority_queue: HashMap<T, VecDeque<Task<T>>>,

    // gid => (running_count,high_priority_queue_count)
    group_statistics: HashMap<T, GroupStatisticsItem>,

    // The maximum number of threads that each group can run when the pool is busy.
    // Each value in `group_statistics` shouldn't be bigger than this value.
    group_concurrency_limit: usize,
}

impl<T: Debug + Hash + Eq + Ord + Send + Clone> BigGroupThrottledQueue<T> {
    pub fn new(group_concurrency_limit: usize) -> BigGroupThrottledQueue<T> {
        BigGroupThrottledQueue {
            high_priority_queue: BinaryHeap::new(),
            low_priority_queue: HashMap::new(),
            group_statistics: HashMap::new(),
            group_concurrency_limit: group_concurrency_limit,
        }
    }

    // Try push into high priority queue. Return none on success,
    // return ReachConcurrencyLimit(task) on failed.
    #[inline]
    fn try_push_into_high_priority_queue(&mut self,
                                         task: Task<T>)
                                         -> Result<(), ReachConcurrencyLimit<Task<T>>> {
        let mut statistics = self.group_statistics
            .entry(task.gid.clone())
            .or_insert(GroupStatisticsItem::new());
        if statistics.sum() >= self.group_concurrency_limit {
            return Err(ReachConcurrencyLimit(task));
        }
        self.high_priority_queue.push(task);
        statistics.high_priority_queue_count += 1;
        Ok(())
    }

    #[inline]
    fn pop_from_low_priority_queue(&mut self) -> Option<Task<T>> {
        let gid = {
            // Groups in low_priority_queue wouldn't too much, so iterate the map
            // is quick.
            let best_group = self.low_priority_queue
                .iter()
                .map(|(gid, low_priority_queue)| {
                    (self.group_statistics[gid].sum(), low_priority_queue[0].id, gid)
                })
                .min();
            if let Some((_, _, gid)) = best_group {
                gid.clone()
            } else {
                return None;
            }
        };

        let task = self.pop_from_low_priority_queue_by_gid(&gid);
        Some(task)
    }

    #[inline]
    fn pop_from_low_priority_queue_by_gid(&mut self, gid: &T) -> Task<T> {
        let (empty_after_pop, task) = {
            let mut waiting_tasks = self.low_priority_queue.get_mut(gid).unwrap();
            let task = waiting_tasks.pop_front().unwrap();
            (waiting_tasks.is_empty(), task)
        };

        if empty_after_pop {
            self.low_priority_queue.remove(gid);
        }
        task
    }
}

impl<T: Hash + Eq + Ord + Send + Clone + Debug> ScheduleQueue<T> for BigGroupThrottledQueue<T> {
    fn push(&mut self, task: Task<T>) {
        if let Err(ReachConcurrencyLimit(task)) = self.try_push_into_high_priority_queue(task) {
            self.low_priority_queue
                .entry(task.gid.clone())
                .or_insert_with(VecDeque::new)
                .push_back(task);
        }
    }

    fn pop(&mut self) -> Option<Task<T>> {
        if let Some(task) = self.high_priority_queue.pop() {
            let mut statistics = self.group_statistics.get_mut(&task.gid).unwrap();
            statistics.high_priority_queue_count -= 1;
            return Some(task);
        } else if let Some(task) = self.pop_from_low_priority_queue() {
            return Some(task);
        }
        None
    }

    fn on_task_started(&mut self, gid: &T) {
        let mut statistics =
            self.group_statistics.entry(gid.clone()).or_insert(GroupStatisticsItem::new());
        statistics.running_count += 1
    }

    fn on_task_finished(&mut self, gid: &T) {
        let count = {
            let mut statistics = self.group_statistics.get_mut(gid).unwrap();
            statistics.running_count -= 1;
            statistics.sum()
        };
        if count == 0 {
            self.group_statistics.remove(gid);
        } else if count >= self.group_concurrency_limit {
            // If the number of running tasks for this group is big enough.
            return;
        }

        if !self.low_priority_queue.contains_key(gid) {
            return;
        }

        // If the value of `group_statistics[gid]` is not big enough, pop
        // a task from `low_priority_queue[gid]` and push it into `high_priority_queue`.
        let group_task = self.pop_from_low_priority_queue_by_gid(gid);
        self.try_push_into_high_priority_queue(group_task).unwrap();
    }
}

struct TaskPool<Q, T> {
    next_task_id: u64,
    task_queue: Q,
    marker: PhantomData<T>,
    stop: bool,
    receiver: Receiver<Task<T>>,
}

impl<Q: ScheduleQueue<T>, T: Debug> TaskPool<Q, T> {
    fn new(queue: Q, receiver: Receiver<Task<T>>) -> TaskPool<Q, T> {
        TaskPool {
            next_task_id: 0,
            task_queue: queue,
            marker: PhantomData,
            stop: false,
            receiver: receiver,
        }
    }

    fn on_task_finished(&mut self, gid: &T) {
        self.task_queue.on_task_finished(gid);
    }

    fn on_task_started(&mut self, gid: &T) {
        self.task_queue.on_task_started(gid);
    }

    fn pop_task(&mut self) -> Option<Task<T>> {
        let task = self.task_queue.pop();
        if task.is_none() {
            self.try_fill_queue(); // try fill queue when queue is empty.
            return self.task_queue.pop();
        }
        task
    }

    fn try_fill_queue(&mut self) {
        loop {
            match self.receiver.try_recv() {
                Ok(mut task) => {
                    task.id = self.next_task_id;
                    self.next_task_id += 1;
                    self.task_queue.push(task);
                }
                _ => {
                    break;
                }
            };
        }
    }

    #[inline]
    fn stop(&mut self) {
        self.stop = true;
    }

    #[inline]
    fn is_stopped(&self) -> bool {
        self.stop
    }
}

/// `ThreadPool` is used to execute tasks in parallel.
/// Each task would be pushed into the pool, and when a thread
/// is ready to process a task, it will get a task from the pool
/// according to the `ScheduleQueue` provided in initialization.
pub struct ThreadPool<Q, T> {
    task_pool: Arc<(Mutex<TaskPool<Q, T>>, Condvar)>,
    threads: Vec<JoinHandle<()>>,
    task_count: Arc<AtomicUsize>,
    sender: Sender<Task<T>>,
}

impl<Q, T> ThreadPool<Q, T>
    where Q: ScheduleQueue<T> + Send + 'static,
          T: Hash + Eq + Send + Clone + 'static + Debug + Copy
{
    pub fn new(name: String, num_threads: usize, queue: Q) -> ThreadPool<Q, T> {
        assert!(num_threads >= 1);
        let (sender, receiver) = channel::<Task<T>>();
        let task_pool = Arc::new((Mutex::new(TaskPool::new(queue, receiver)), Condvar::new()));
        let mut threads = Vec::with_capacity(num_threads);
        let task_count = Arc::new(AtomicUsize::new(0));
        // Threadpool threads
        for _ in 0..num_threads {
            let tasks = task_pool.clone();
            let task_num = task_count.clone();
            let thread = Builder::new()
                .name(name.clone())
                .spawn(move || {
                    let mut worker = Worker::new(tasks, task_num);
                    worker.run();
                })
                .unwrap();
            threads.push(thread);
        }

        ThreadPool {
            task_pool: task_pool,
            threads: threads,
            task_count: task_count,
            sender: sender,
        }
    }

    pub fn execute<F>(&mut self, gid: T, job: F)
        where F: FnOnce() + Send + 'static
    {
        // let &(ref lock, ref cvar) = &*self.task_pool;
        // let mut meta = lock.lock().unwrap();
        // meta.push_task(gid, job);
        // self.task_count.fetch_add(1, AtomicOrdering::SeqCst);
        // cvar.notify_one();
        let task = Task::new(0, gid, job);
        self.sender.send(task).unwrap();
        self.task_count.fetch_add(1, AtomicOrdering::SeqCst);
        let &(_, ref cvar) = &*self.task_pool;
        cvar.notify_one();
    }

    #[inline]
    pub fn get_task_count(&self) -> usize {
        self.task_count.load(AtomicOrdering::SeqCst)
    }

    pub fn stop(&mut self) -> Result<(), String> {
        {
            let &(ref lock, ref cvar) = &*self.task_pool;
            let mut tasks = lock.lock().unwrap();
            tasks.stop();
            cvar.notify_all();
        }
        let mut err_msg = String::new();
        for t in self.threads.drain(..) {
            if let Err(e) = t.join() {
                write!(&mut err_msg, "Failed to join thread with err: {:?};", e).unwrap();
            }
        }
        if !err_msg.is_empty() {
            return Err(err_msg);
        }
        Ok(())
    }
}

// Each thread has a worker.
struct Worker<Q, T> {
    task_pool: Arc<(Mutex<TaskPool<Q, T>>, Condvar)>,
    task_count: Arc<AtomicUsize>,
}

impl<Q, T> Worker<Q, T>
    where Q: ScheduleQueue<T>,
          T: Debug + Clone + Copy
{
    fn new(task_pool: Arc<(Mutex<TaskPool<Q, T>>, Condvar)>,
           task_count: Arc<AtomicUsize>)
           -> Worker<Q, T> {
        Worker {
            task_pool: task_pool,
            task_count: task_count,
        }
    }

    // `get_next_task` return `None` when `task_pool` is stopped.
    #[inline]
    fn get_next_task(&self, last_gid: Option<T>) -> (Option<Task<T>>, bool) {
        // try to receive notification.
        let &(ref lock, ref cvar) = &*self.task_pool;

        let mut task_pool = lock.lock().unwrap();
        if last_gid.is_some() {
            task_pool.on_task_finished(&last_gid.unwrap());
        }
        loop {
            if task_pool.is_stopped() {
                return (None, true);
            }
            if let Some(task) = task_pool.pop_task() {
                // `on_task_started` should be here since:
                //  1. To reduce lock's time;
                //  2. For some schedula_queue,on_task_started should be
                //  in the same lock with `pop_task` for the thread safety.
                task_pool.on_task_started(&task.gid);
                return (Some(task), false);
            }
            task_pool = cvar.wait(task_pool).unwrap();
        }
        // return (None,task_pool.is_stopped())

        // loop {
        //     if task_pool.is_stopped() {
        //         return None;
        //     }
        //     if let Some(task) = task_pool.pop_task() {
        //         // `on_task_started` should be here since:
        //         //  1. To reduce lock's time;
        //         //  2. For some schedula_queue,on_task_started should be
        //         //  in the same lock with `pop_task` for the thread safety.
        //         task_pool.on_task_started(&task.gid);
        //         return Some(task);
        //     }
        //     // wait for new task
        //     task_pool = cvar.wait(task_pool).unwrap();
        // }
    }

    fn run(&mut self) {
        let mut last_gid = None;
        // Start the worker. Loop breaks when receive stop message.
        loop {
            let (task, stop) = self.get_next_task(last_gid);
            if stop {
                break;
            }
            if task.is_none() {
                continue;
            }
            let task = task.unwrap();
            // Since tikv would be down when any panic happens,
            // we don't need to process panic case here.
            last_gid = Some(task.gid.clone());
            (task.task)();
            //  let &(ref lock, _) = &*self.task_pool;

            // let mut task_pool = lock.lock().unwrap();
            // task_pool.on_task_finished(&task.gid);
            self.task_count.fetch_sub(1, AtomicOrdering::SeqCst);
        }
    }
}
