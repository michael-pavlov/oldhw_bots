create table qbot_answers
(
	message_id bigint not null
		primary key,
	question_id bigint not null,
	answer_text varchar(10000) null,
	answer_status varchar(100) null,
	ans_user_id bigint not null,
	answer_time timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP
)
engine=InnoDB
;

create table qbot_questions
(
	user_id bigint not null
		primary key,
	question_id bigint not null,
	question_text varchar(10000) null,
	question_tags varchar(1000) null,
	constraint user_id
		unique (user_id)
)
engine=InnoDB
;

create table qbot_sent_questions
(
	question_id bigint not null
		primary key,
	reci_user_id bigint not null,
	questions_status varchar(100) null,
	sent_time timestamp default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP
)
engine=InnoDB
;

create table qbot_users
(
	name varchar(30) null,
	id varchar(30) not null
		primary key,
	tags varchar(10000) null,
	profile_urls varchar(10000) null
)
engine=InnoDB
;
