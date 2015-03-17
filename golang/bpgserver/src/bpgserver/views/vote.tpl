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
    <form id="test" action="/t/vote/{{.vpath}}" method="POST">
    <!--a&{Name:myphoto_1.jpg Path:/static/img/1/jpgs/myphoto_1.jpg SizeStr:29K Size:30597}-->
    {{range $key,$val := .pics}}
	<table border="1" >
    <tr>{{$key}}</tr>
	<tr>
	<td><a href="{{$val.Bpg.Path}}">1</a>  <br>
	<img src="{{$val.Bpg.Path}}">
    </td>
  	<td><a href="{{$val.Jpg.Path}}">2</a> <br>
	<img src="{{$val.Jpg.Path}}">
        </td>
	
	<td><a href="{{$val.Webp.Path}}">3</a> <br>
	<img src="{{$val.Webp.Path}}">
        </td> 
	</tr>
    <tr> 
    <th colspan="3" cellpadding="10" style='color:blue' align="center">
    quality order:
    <select id="{{$key}}" name="{{$key}}" >
    <option value="same">一样好</option>
    <option value="bpg">1 最好 </option>
    <option value="jpg">2 最好 </option>
    <option value="webp">3 最好</option>
    </select>
    </th>
    </tr>
	</table>
<hr/>
   {{end}} 
   <table>
   <tr colspan="3" cellpadding="10" style='color:blue' align="center">
   <input type="submit" style="color:red;width:100;height:50;"  value="Submit" name="Submit">
   </tr>
   </table>
   </form>
    </body>
<html>

