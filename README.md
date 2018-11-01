
> 通过廖雪峰博客Python文章实践的一个小博客，感谢廖大:)

```
www/config/env.bak -> env.py 配置文件
www/db/table.sql 默认数据表
log/ 日志文件
......
```

### todo list    
- [x] 完善添加大日志错误（next_id打成了next_id()），编辑日志错误（此处日志指文章）
- [x] 图片管理。写md肯定需要解决图片问题，找到[markdown-helper](https://github.com/wuchangfeng/markdown-helper) 通过七牛云传图获取URL，完美。p.s. 有以前建的一个存储空间，删掉之后再建了一个提醒需要认证，但是认证需要手持身份证太麻烦，转又拍云了。
- [x] markdown ` ``` ` 解析失败，换了[mistune](https://github.com/lepture/mistune), 添加了[markdown样式]( https://github.com/zhangjikai/markdown-css)。[Python下Markdnown解析踩的小坑](https://mervinz.me/post/9/)
- [x] 配置`logging文件`记录日志并滚动2018-10-31
- [ ] markdown mistune + task list
- [ ] markdown 代码颜色
- [ ] 发布jenkins
- [ ] 优化路由/handlers, 单独出类
- [ ] 评论
- [ ] 用户名登录
- [ ] 稍微学一点VUE， 添加功能
- [ ] 添加工具箱功能
- [ ] 同步发布到博客园或者从博客园同步拉取
