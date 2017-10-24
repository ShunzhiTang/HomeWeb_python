-- 手写创建表的SQL语句

drop database if exists homePage;

create database homePage;

use homePage;

-- grant 权限 on 数据库.* to 用户名@登录主机 identified by "密码";
-- 为用户授权 如果想指定部分权限给一用户
grant select ,insert,update,delete on homePage.* to 'www-data'@'localhost' identified by 'www-data';

-- create users table
create table users(
  `id` varchar(50) not null,
  `email` varchar(50) not null,
  `passwd` varchar(50) not null,
  `admin` bool not null,
  `name` varchar(50) not null,
  `image` varchar(50) not null,
  `created_at` real not null,
  unique key `idx_email` (`email`),key `idx_created_at` (`created_at`),
  primary key(`id`)
)engine=innodb default charset=utf8;

-- create blogs table
create table blogs(
  `id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(50) not null,
  `name` varchar(50) not null,
  `summary` varchar(50) not null,
  `content` varchar(50) not null,
  `created_at` real not null,
  unique key `idx_created_at` (`created_at`),
  primary key(`id`)
)engine=innodb default charset=utf8;

-- create comments table
create table comments(
  `id` varchar(50) not null,
  `blog_id` varchar(50) not null,
  `user_id` varchar(50) not null,
  `user_name` varchar(50) not null,
  `user_image` varchar(50) not null,
  `content` varchar(50) not null,
  `created_at` real not null,
  unique key `idx_created_at` (`created_at`),
  primary key(`id`)
)engine=innodb default charset=utf8;

-- 存储引擎是 innodb