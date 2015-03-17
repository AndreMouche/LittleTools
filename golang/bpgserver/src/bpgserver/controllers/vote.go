package controllers

import (
	"github.com/astaxie/beego"
    "bpgserver/models"
    "fmt"
)

type VoteController struct {
	beego.Controller
    
}
/*var  rootPath = "/styx/home/hzwuxuelian/go_root/go_project/src/bpgserver"//"/home/fun/go_root/go_project/src/bpgserver";
var  staticPath = rootPath + "/static"
var  imgsPath = staticPath+"/img"*/
func (c *VoteController) Get() {
    curId := c.Ctx.Input.Param(":id")
    curPath := imgsPath + "/" + curId;
    fmt.Println("Cur Path:"+ curPath);
    pics,err := models.GetPicClasses(curPath)
    if (len(pics) == 0 || err != nil) {
      c.Data["Path"] = curId
      c.TplNames = "notfoud.tpl"
      return
    }
	c.Data["vpath"] = curId
	c.Data["Email"] = "astaxie@gmail.com"
    c.Data["pics"] = pics;
	c.TplNames = "vote.tpl"
}

func (c *VoteController)Post() {
     curPath := c.Ctx.Input.Param(":id")
     req := c.Ctx.Input.Request;
     req.ParseForm()
     forms := req.Form
     curMap := make(map[string]string)
     for key,_:=range forms {
        curMap[key] = forms.Get(key) 
     }
     client:=req.RemoteAddr
     err := models.HandleOneReq(client,curPath,curMap)
     c.Data["rpath"]=curPath
     c.Data["note"] = ""
     if err != nil {
        c.Data["note"] = err.Error()
     }
     c.TplNames = "thx.tpl"    
}
