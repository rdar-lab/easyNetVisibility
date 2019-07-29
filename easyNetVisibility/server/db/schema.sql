create database net_visibility;

use net_visibility

create table devices(
	device_id MEDIUMINT NOT NULL AUTO_INCREMENT,
	hostname varchar(30),
	nickname varchar(30),
	ip varchar(30),
	mac varchar(30),
	vendor varchar(30),
	first_seen timestamp not null,
	last_seen timestamp not null,
	primary key (device_id)
);

create table sensors(
	sensor_id MEDIUMINT NOT NULL AUTO_INCREMENT,
	mac varchar(30) NOT NULL,
	hostname varchar(30),
	first_seen timestamp not null,
	last_seen timestamp not null,
	primary key (sensor_id)
);
	
create table ports(
	port_id MEDIUMINT NOT NULL AUTO_INCREMENT,
	device_id MEDIUMINT NOT NULL,
	port_num MEDIUMINT NOT NULL,
	protocol varchar(30),
	name varchar(30),
	product varchar(30),
	version varchar(30),
	first_seen timestamp not null,
	last_seen timestamp not null,
	primary key (port_id),
	FOREIGN KEY fk_device_port(device_id) REFERENCES devices(device_id) ON DELETE CASCADE ON UPDATE CASCADE
);
