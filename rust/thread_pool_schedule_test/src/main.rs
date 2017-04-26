// Copyright 2017 PingCAP, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// See the License for the specific language governing permissions and
// limitations under the License.
#![crate_type = "lib"]
#![feature(fnbox)]
extern crate ordermap;
extern crate threadpool;
use std::time::{self, Duration};
use std::sync::mpsc::channel;
#[macro_use]
pub mod taskpool;
use taskpool::{ThreadPool as TaskPool, BigGroupThrottledQueue, FIFOQueue, SpeedupSmallGroups,
               ScheduleQueue};
use threadpool::ThreadPool as OriginThreadPool;

fn test_task_pool<Q>(task_num: u64, mut task_pool: TaskPool<Q, u64>)
    where Q: ScheduleQueue<u64> + Send + 'static
{
    let start = time::SystemTime::now();
    println!("start at {:?}", start);
    let (jtx, jrx) = channel();
    let recv_timeout_duration = Duration::from_secs(2);
    for group_id in 0..task_num {
        let sender = jtx.clone();
        task_pool.execute(group_id, move || {
             let value = do_task();
            sender.send(value).unwrap();
        });
    }

    for _ in 0..task_num {
        jrx.recv_timeout(recv_timeout_duration).unwrap();
    }

    let end = time::SystemTime::now();
    println!("finished at {:?} cost {:?}",
             end,
             end.duration_since(start).unwrap());
    task_pool.stop().unwrap();
}

fn test_origin_pool(concurrency: usize, task_num: u64) {
    let start = time::SystemTime::now();
    println!("start at {:?}", start);
    let name = String::from("test_tasks_with_same_cost");
    let task_pool = OriginThreadPool::new_with_name(name, concurrency);
    let (jtx, jrx) = channel();
    let recv_timeout_duration = Duration::from_secs(2);
    // push 1 task for each group_id in [0..task_num) into pool.
    for _ in 0..task_num {
        let sender = jtx.clone();
        task_pool.execute(move || {
            let value = do_task();
            sender.send(value).unwrap();
        });
    }

    for _ in 0..task_num {
        jrx.recv_timeout(recv_timeout_duration).unwrap();
    }
    let end = time::SystemTime::now();
    println!("finished at {:?} cost {:?}",
             end,
             end.duration_since(start).unwrap());
}

fn do_task()->u64 {
    let mut value = 0 as u64;
    for id in 0..10 {
        value += id;
    }
    value
}

fn main() {
    let concurrency = 8;
    let name = String::from("test_tasks_with_same_cost");
    let big_group_throttled_queue =
        TaskPool::new(name.clone(),
                      concurrency,
                      BigGroupThrottledQueue::new((concurrency / 4) as usize));

    let task_num = 100000;
    println!("heap test");
    test_task_pool(task_num, big_group_throttled_queue);

    println!("queue test");
    let speed_small_groups = TaskPool::new(name.clone(),
                                           concurrency,
                                           SpeedupSmallGroups::new((concurrency / 4) as usize));


    test_task_pool(task_num, speed_small_groups);
    println!("FiFO test");
    let fifo_groups = TaskPool::new(name, concurrency, FIFOQueue::new());
    test_task_pool(task_num, fifo_groups);

    println!("origin test");
    test_origin_pool(8, task_num);
}
