package main

import (
	"fmt"
	"net/http"
	"time"
)

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Receive a request", r.URL, r.RemoteAddr)
	fmt.Fprintf(w, "aaaa")
	time.Sleep(time.Second)
	//r.Close()
	fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
}

func main() {
	http.HandleFunc("/", handler)
	http.ListenAndServe(":8588", nil)
}
