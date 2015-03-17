package main

import (
	"fmt"
	"os"
	"path/filepath"
    "strings"
)

type Item struct {
    Name string
    Path string 
    SizeStr string
    Size  int64
}

func NewItem(name,path string,size int64) (item *Item) {
    item = &Item{
       Name:name,
       Path:path,
       Size:size,
    }
    curPath := []byte(path)[strings.Index(path,"/static"):]
    item.Path = string(curPath)

    if(size < 1024) {
       item.SizeStr = fmt.Sprintf("%d",size)
       return 
    }
    sizeInK := size/1024.0
    fmt.Println(sizeInK)
    item.SizeStr = fmt.Sprintf("%+vK",sizeInK)
    return 
}

func (item *Item)getNameAndType()(name,ctype string){
   strs := strings.Split(item.Name,".")
   fmt.Println(item.Name)
   fmt.Printf("%+v\n",strs)
   if(len(strs) < 2) {
     return  "", ""
   }
   return  strs[0],strs[1]
}

type  PicClass struct {
   Jpg  *Item
   Webp *Item 
   Bpg  *Item
}

func GetPicClasses(fullPath string)(pics map[string]*PicClass, err error) {
    files,err := ListFiles(fullPath)
    if err != nil {
       return nil,err
    }

    pics = make(map[string]*PicClass)
    for _,file := range files {
        key,ctype :=  file.getNameAndType();
       _,ok := pics[key]
       if !ok {
           pics[key] = &PicClass{}
       }

       if(ctype == "bpg") {
           pics[key].Bpg = file;
       } else if(ctype == "webp"){
           pics[key].Webp = file;
       } else if(ctype == "jpg"){
           pics[key].Jpg = file;
       }
       
    }
    
   return
}

func ListFiles(fullPath string)(files map[string]*Item,err error) {

    files = make(map[string]*Item)
	filepath.Walk(fullPath, func(path string, fi os.FileInfo, err error) error {
		if nil == fi {
			return err
		}
		if fi.IsDir() {
			return nil
		}
        files[fi.Name()] = NewItem(fi.Name(),path,fi.Size())  
	//	name := fi.Name()
        //fmt.Println(path);
        fmt.Println("filename:",path,",size:",fi.Size())
		return nil
	})
    return
}

func main() {
	var path string
	if len(os.Args) > 1 {
		path = os.Args[1]
	} else {
		path, _ = os.Getwd()
	}
   
    files,_ := GetPicClasses(path);//ListFiles(path)
    for key,value:=range files{
        fmt.Println(key)
        fmt.Printf("%+v\n",value.Jpg)
        fmt.Printf("%+v\n",value.Webp)
        fmt.Printf("%+v\n",value.Bpg)
        //fmt.Println("path:",value.Path,",size:",value.SizeStr)
    }

	fmt.Println("done!")
}
