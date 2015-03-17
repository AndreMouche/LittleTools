package controllers

import (
	"github.com/astaxie/beego"
)

type BPGController struct {
	beego.Controller
}

func (c *BPGController) Get() {
	c.Data["bpg"] = "inni"
	c.Data["Email"] = "astaxie@gmail.com"
	c.TplNames = "index.tpl"
}
