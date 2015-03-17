package models

import (
    "sync"
    "fmt"
)

var locker *sync.Mutex
//var VResult map[string]*VItemGroup 
var  Reqs  *ClienReq

type  RItem struct{
   Path string
   Form  map[string]string 
}

type ClienReq struct {
   Reqs map[string]*RItem
   locker *sync.Mutex
}

type VItemGroup struct {
   Path string 
   VInfo map[string]*VItem;
   Total int
}

func init() {
    Reqs = &ClienReq{
        Reqs:make(map[string]*RItem),
        locker:new(sync.Mutex),
    }

  //  VResult = make(map[string]*VItemGroup)
    locker = new(sync.Mutex)
}

func HandleOneReq(client,path string,form  map[string]string) (err error) {
    fmt.Printf("client:%s,path:%s,form:%+v",client,path,form)
   fmt.Println("")
   Reqs.locker.Lock()
   defer Reqs.locker.Unlock()
   key := client + ":" + path
   _,ok := Reqs.Reqs[key]
   if ok {
       err = fmt.Errorf("Same vote existed,we will use current vote instead history data.")
       delete(Reqs.Reqs,key)
   }
   Reqs.Reqs[key] = &RItem{
      Path:path,
      Form:form,
   }
   return err;
}

type VItem struct {
   Name string 
   Total int
   Det  map[string]int 
}

func (item *VItem) Handle(fname string) (err error) {
     _,ok := item.Det[fname]
     if !ok {
         item.Det[fname] = 1
     } else {
         item.Det[fname] += 1;
     }
     item.Total +=1
     return nil
}

func (g *VItemGroup) Handle(form map[string] string) (err error) {
    g.Total += 1
    for key,value := range form {
        _,ok := g.VInfo[value]
        if !ok {
           g.VInfo[value] =  &VItem{
              Name:value,
              Total:0,
              Det:make(map[string]int),
           }
        }
        g.VInfo[value].Handle(key)
    }
    return nil
}


func GetVoteResult(rpath string) (map[string]*VItemGroup,error) {
    Reqs.locker.Lock()
    defer Reqs.locker.Unlock();
    vResult := make(map[string]*VItemGroup);
    for _,cItem := range Reqs.Reqs {
        path := cItem.Path 
        _,ok :=  vResult[path]
        if !ok {
            vResult[path] = &VItemGroup{
                Path:path,
                VInfo:make(map[string]*VItem),
                Total:0,
            }
        }

        vResult[path].Handle(cItem.Form)
    }
    return  vResult,nil
   // return json.Marshal(VResult)
    
}

