package controllers

import (
	"github.com/astaxie/beego"
    "bpgserver/models"
    "fmt"
)

type MainController struct {
	beego.Controller
}
var  RootPath = "/styx/home/hzwuxuelian/go_root/go_project/src/bpgserver"//"/home/fun/go_root/go_project/src/bpgserver";
var  staticPath string 
var  imgsPath  string 

func init(){
   SetRootPath(RootPath)
}

func SetRootPath(rootPath string) {
     RootPath = rootPath 
     staticPath = RootPath + "/static"
     imgsPath = staticPath+"/img"
}

func (c *MainController) Get() {
    curId := c.Ctx.Input.Param(":id")
    curPath := imgsPath + "/" + curId;
    fmt.Println("Cur Path:"+ curPath);
    pics,err := models.GetPicClasses(curPath)
    if (len(pics) == 0 || err != nil) {
      c.Data["Path"] = curId
      c.TplNames = "notfoud.tpl"
      return
    }
	c.Data["Website"] = "beego.me"
	c.Data["Email"] = "astaxie@gmail.com"
    c.Data["pics"] = pics;
	c.TplNames = "index.tpl"
}
