package main

import (
	"crypto/hmac"
	"crypto/sha1"
	"encoding/base64"
	"fmt"
	"math/rand"
	"net/url"
	"sort"
	"strings"
	"time"
)

/**
https://www.qcloud.com/doc/api/258/%E6%8E%A5%E5%8F%A3%E9%89%B4%E6%9D%83
腾讯云接口签名算法实现
*/

const SecretKeyId = "xxx"
const SecretKey = "xxx"

const RequestPath = "/v2/index.php"
const RegionGz = "gz"

type QTenQuery struct {
	params         map[string]string
	secretKey      string
	method         string
	host           string
	sortedQueryStr string
}

func NewQTenQuery(method, host, action, region, secretId, secretKey string) *QTenQuery {
	query := &QTenQuery{
		params: map[string]string{
			"Action":    action,
			"Region":    region,
			"Timestamp": fmt.Sprintf("%v", time.Now().Unix()),
			"Nonce":     fmt.Sprintf("%v", rand.Int63()),
			"SecretId":  secretId,
		},
		secretKey: secretKey,
		method:    method,
		host:      host,
	}
	return query
}

func (self *QTenQuery) AddParams(key, value string) {
	self.params[key] = value
}

const TagSignature = "Signature"

/**
获取签名原文字符串中的参数，即对参数按字典序排列
*/
func (self *QTenQuery) sortedQueryString() {
	delete(self.params, TagSignature)
	//sortedParams := SortMapKey(self.params)
	querys := make([]string, len(self.params), len(self.params))
	id := 0
	for key, value := range self.params {
		value = strings.Replace(value, ".", "_", 0)
		key = strings.Replace(key, ".", "_", 0)
		querys[id] = fmt.Sprintf("%s=%v", key, value)
		id++
	}
	sort.Strings(querys)
	self.sortedQueryStr = strings.Join(querys, "&")
	fmt.Println("sortedKey:", self.sortedQueryStr)
}

/**
计算签名
*/
func (self *QTenQuery) computeSignature() {
	self.sortedQueryString()
	sign_str := fmt.Sprintf("%s%s%s?%s", self.method, self.host, RequestPath, self.sortedQueryStr)
	fmt.Println("sign_before:", sign_str)
	h := hmac.New(sha1.New, []byte(self.secretKey))
	h.Write([]byte(sign_str))
	token := base64.StdEncoding.EncodeToString(h.Sum(nil))
	fmt.Println("token:", token)
	self.params[TagSignature] = token

}

/**
* 获取认证后的URL
 */
func (self *QTenQuery) GetUrl() string {
	self.computeSignature()
	querys := make([]string, len(self.params), len(self.params))
	id := 0
	for key, value := range self.params {
		querys[id] = fmt.Sprintf("%s=%v", key, url.QueryEscape(value))
		id++
	}

	queryStr := strings.Join(querys, "&")

	return fmt.Sprintf("https://%s%s?%s", self.host, RequestPath, queryStr)

}

func CreateStream() {
	query := NewQTenQuery("GET", "cvm.api.qcloud.com", "DescribeInstances", RegionGz, SecretKeyId, SecretKey)
	query.AddParams("offset", "0")
	query.AddParams("limit", "20")
	query.AddParams("instanceIds.0", "ins-09dx96dg")
	//query.AddParams("sourceList.1.type", "1")

	fmt.Println(query.GetUrl())

}

func main() {
	CreateStream()
}
