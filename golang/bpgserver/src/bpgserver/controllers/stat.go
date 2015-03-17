package controllers

import (
	"github.com/astaxie/beego"
    "bpgserver/models"
)

type StatController struct {
	beego.Controller
    
}
/*var  rootPath = "/styx/home/hzwuxuelian/go_root/go_project/src/bpgserver"//"/home/fun/go_root/go_project/src/bpgserver";
var  staticPath = rootPath + "/static"
var  imgsPath = staticPath+"/img"*/
func (c *StatController) Get() {
    curId := c.Ctx.Input.Param(":id")
    stat,_ := models.GetVoteResult(curId)
    c.Data["json"] = stat;
	c.ServeJson()
}


