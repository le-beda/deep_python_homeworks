create table users (
    username text primary key not null unique,
    password text not null,
    name text not null
);

create table resumes (
    username text primary key not null unique,
    full_name text,
    date_of_birth DATETIME,
    education text,
    skills text,
    personal_info text
);
