package main

import (
	"bpgserver/controllers"
	_ "bpgserver/routers"
	"flag"
	"github.com/astaxie/beego"
    "fmt"
)

var RootPath = flag.String("d", "", "project path,include ./static/")

func main() {
	flag.Parse()
	if RootPath == nil || len(*RootPath) == 0 {
		panic("Illegal RootPath")
	}
    fmt.Println(*RootPath)
	controllers.SetRootPath(*RootPath)
	beego.Router("/t/result/?:id", &controllers.MainController{})
	beego.Router("/t/vote/?:id", &controllers.VoteController{})
	beego.Router("/t/stat/?:id", &controllers.StatController{})
	beego.Run()
}
