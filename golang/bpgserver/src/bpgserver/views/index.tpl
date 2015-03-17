<!DOCTYPE html>
<html> 
<title>
 Comparation between jpg,bpg,webp with similar file size
</title>
<head>
<meta charset="UTF-8"> 
<!-- The following scripts are available (sorted by increasing size):
	bpgdec8.js  : 8 bit only, no animation
	bpgdec.js   : up to 14 bits, no animation
	bpgdec8a.js : 8 bit only, animations
	-->
    <script type="text/javascript" src="/static/js/bpg/bpgdec8a.js"></script>
</head>
	<body>
    <!--a&{Name:myphoto_1.jpg Path:/static/img/1/jpgs/myphoto_1.jpg SizeStr:29K Size:30597}-->
    {{range $key,$val := .pics}}
	<table >
    <tr>{{$key}}</tr>
	<tr>
	<td><a href="{{$val.Bpg.Path}}">bpg</a>:{{$val.Bpg.SizeStr}}({{$val.Bpg.Size}})  <br>
	<img src="{{$val.Bpg.Path}}">
    </td>
  	<td><a href="{{$val.Jpg.Path}}">jpg</a>:{{$val.Jpg.SizeStr}}({{$val.Jpg.Size}}) <br>
	<img src="{{$val.Jpg.Path}}">
        </td>
	
	<td><a href="{{$val.Webp.Path}}">webp</a>:{{$val.Webp.SizeStr}}({{$val.Webp.Size}})<br>
	<img src="{{$val.Webp.Path}}">
        </td> 
	</tr>
	</table>
<hr/>
   {{end}} 
    </body>
<html>

