CREATE TABLE IF NOT EXISTS logins (
                                    username VARCHAR(10) PRIMARY KEY,
                                    password VARCHAR(102));

CREATE TABLE IF NOT EXISTS messages (
                                    author VARCHAR(10) ,
                                     recipient VARCHAR(10),
                                     text TEXT,
                                     time INTEGER,
                                     unread INT TRUE);

CREATE TABLE IF NOT EXISTS chats ( user VARCHAR(10),
                                   companion VARCHAR(10),
                                   last_msg_time INT,
                                   unread INT FALSE);