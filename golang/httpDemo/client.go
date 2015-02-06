package main

import (
	"fmt"
	"net/http"
	"strings"
	"sync"
)

func headTest(id int, req *http.Request, client *http.Client) {
	req.Header.Set("RequestId", fmt.Sprintf("%d", id))
	rsp, err := client.Do(req)
	if err != nil {
		var errStr string
		errStr = err.Error()
		if strings.Contains(errStr, "connection reset by peer") {
			return
		}
		fmt.Println(id, err)
		return
	}
	fmt.Println(id, "rsp", rsp.StatusCode)
	//fmt.Println(id, "headers", rsp.Header)
	rsp.Body.Close()
}

func main() {
	//time.Sleep(time.Hour)
	fmt.Println("Hello world!")
	//postUrl := "http://httpbin.org/get"
	headUrl := "http://172.17.2.201:8588/AndreMouche"
	req, err := http.NewRequest("HEAD", headUrl, nil)
	if err != nil {
		fmt.Println(err)
		return
	}
	var client *http.Client
	client = &http.Client{}

	wg := sync.WaitGroup{}

	for id := 0; id < 1000; id++ {
		wg.Add(1)
		go func(id int) {
			headTest(id, req, client)
			wg.Done()
		}(id)
	}
	wg.Wait()
	fmt.Println("Finished")
	print("haqiqiqiqiqi\n")
}
