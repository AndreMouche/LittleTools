package main

import (
	"fmt"
	"os"
	"path/filepath"
    "strings"
    "sort"
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
    totalJ := int64(0)
    totalW := int64(0)
    totalB := int64(0)
    results := []string{}
    for key,value:=range files{
        //fmt.Println(key)
        //fmt.Printf("%+v\n",value.Jpg)
        //fmt.Printf("%+v\n",value.Webp)
        //fmt.Printf("%+v\n",value.Bpg)
        disB := float64(value.Bpg.Size-value.Jpg.Size)*1.0/float64(value.Jpg.Size)*100.0
        disW := float64(value.Bpg.Size-value.Jpg.Size)*1.0/float64(value.Jpg.Size)*100.0
        fmt.Println(key,"DisB:",disB,",DisW:",disW)
        totalJ += value.Jpg.Size
        totalW += value.Webp.Size 
        totalB += value.Bpg.Size
        //key jpg bpg DisBpg webp DisW  
       // append(results,
       curS := fmt.Sprintf("|%s |%6d |%6d |%-6.2f |%6d |%-6.2f|",key,value.Jpg.Size,value.Bpg.Size,disB,value.Webp.Size,disW)
       results = append(results,curS) 
       fmt.Println(curS)
    }
    fmt.Println("TotalJ:" ,totalJ, ",totalB:",totalB,",totalW:",totalW)
    disB := float64(totalB - totalJ)/float64(totalJ)*100.0
    disW := float64(totalW - totalJ)/float64(totalJ)*100.0

    curS := fmt.Sprintf("|%s |%6d |%6d |%-6.2f |%6d |%-6.2f|","total",totalJ,totalB,disB,totalW,disW)
    results = append(results,curS)
    fmt.Println("DisB:",disB,",DisW:",disW)
	fmt.Println("done!")
    sort.Sort(sort.StringSlice(results)) 
    for _,v := range results {
       fmt.Println(v)
    }
}
