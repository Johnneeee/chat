from app import app,conn
from time import ctime
from flask import request
from apsw import Error
from markupsafe import escape
import flask
from flask_login import login_required, current_user, logout_user, current_user

@app.route('/send', methods=['POST','GET'])
def send():
    try:
        sender = current_user.id
        recipient = request.args.get('recipient')
        recipientstring = recipient.replace(" ", "")        
        recipientstring = recipientstring.lower()
        recipients = recipientstring.split(",")
        ids = ""
        message = request.args.get('message')

        if not sender or not recipient or not message:
            raise Exception(f'ERROR: missing sender, recipient or message')

        if len(recipients) != len(set(recipients)):
            raise Exception(f'ERROR: you have entered the same recipient multiple times')

        for x in range(len(recipients)):    
            if recipients[x] == current_user.id:
                raise Exception(f'ERROR: sorry, you cannot send a message to yourself')

            usercheck = f"SELECT username FROM users WHERE username IN ('{recipients[x]}');"
            c = conn.execute(usercheck)
            rows = c.fetchall()
            c.close()

            if len(rows) == 0:
                raise Exception(f'ERROR: {recipients[x]} is not registered')


            blockedcheck = f"SELECT * FROM blocking WHERE (username = '{recipients[x]}' AND usernameBlocked = '{sender}')"
            c = conn.execute(blockedcheck)
            rowsblockedcheck = c.fetchall()
            c.close()

            if len(rowsblockedcheck) > 0:
                raise Exception(f'ERROR: {recipients[x]} has blocked you')



        for x in range(len(recipients)):
            stmt = f"INSERT INTO messages (sender, recipient, message, timestamp) values ('{sender}', '{recipients[x]}', '{message}', '{ctime()}');"
            conn.execute(stmt)
            ids = ids + str(conn.last_insert_rowid()) + ','

        result = {"sender":sender, "message":message, "recipients":recipientstring, "timestamp":ctime(), "reply":0, "id":ids, "error":"no"}
        return result
    except Exception as e:
        result = {"sender":"", "message":"", "recipients":"", "timestamp":"", "reply":"", "id":"", "error":str(e)}
        return result


@app.route("/allusers")
@login_required
def allusers():
    stmt = f"SELECT username, isActive FROM users"
    try:
        c = conn.execute(stmt)
        rows = c.fetchall()
        result = []
        for row in rows:
            result.append({"user" :escape(row[0]), "isActive":escape(row[1])})
        return result
    except Error as e:
        return (f'{result}ERROR: {e}', 500)


@app.get('/search')
def search():
    query = request.args.get('q') or request.form.get('q') or '*'
    if query == '*':
        stmt = f'''
            SELECT *
            FROM messages WHERE (
                recipient LIKE '{current_user.id}'
                OR sender LIKE '{current_user.id}'
            )
    '''
    else:
        stmt = f'''
        SELECT
        * 
        FROM
        messages
        WHERE
        (
            id LIKE '{query}'
            AND (
                sender LIKE '{current_user.id}'
                OR recipient LIKE '{current_user.id}'
            )
        
            OR (
                recipient LIKE '%{query}%'
                AND sender LIKE '{current_user.id}'
            )
            OR (
                recipient LIKE '{current_user.id}'
                AND sender LIKE '%{query}%'
            )
            OR (
                message LIKE '%{query}%'
                AND (
                sender LIKE '{current_user.id}'
                OR recipient LIKE '{current_user.id}'
                )
            )
        )
        '''
    anns = []
    try:
        c = conn.execute(stmt)
        rows = c.fetchall()
        for row in rows:
            if (escape(row[5]) != 0):
                anns.append({"id":escape(row[0]), "sender":escape(row[1]), "reciever":escape(row[2]), "message":escape(row[3]), "time":escape(row[4]), "reply":escape(row[5])})
            else:
                anns.append({"id":escape(row[0]), "sender":escape(row[1]), "reciever":escape(row[2]), "message":escape(row[3]), "time":escape(row[4]), "reply":escape(row[5])})

        return anns
    except Exception as e:
        return {"sender":"", "reciever":"", "message":"", "time":"", "reply":"", "id":"", "error":str(e)}


@app.route('/reply', methods=['POST','GET'])
def reply():
    try:
        reply = request.args.get('reply')
        sender = current_user.id

        if(reply.isdigit()):
            reply = int(reply)
        else:
            raise Exception(f"ERROR: {reply} has to be an valid integer")
            
        message = request.args.get('message')
        query = f'SELECT sender, recipient FROM messages WHERE id={reply}'
        resultrow = conn.execute(query)
        result = resultrow.fetchall()

        if (len(result) == 0):
            raise Exception(f'ERROR: You have no messages with the given ID')

        recipient = result[0][0]
        sender = result[0][1]
        # print(recipient,sender,current_user.id)
        if(current_user.id != sender):
            raise Exception(f'ERROR: You have no messages with the given ID')

        blockedcheck = f"SELECT * FROM blocking WHERE (username = '{recipient}' AND usernameBlocked = '{sender}')"
        c = conn.execute(blockedcheck)
        rowsblockedcheck = c.fetchall()
        c.close()

        if not message:
            raise Exception(f'ERROR: Missing message')

        if recipient == current_user.id:
            raise Exception(f'ERROR: sorry, you cannot send a message to yourself')
        
        if len(rowsblockedcheck) > 0:
            raise Exception(f'ERROR: {recipient} is blocked, there will the message not be sent.')
        

        stmt = f"INSERT INTO messages (sender, recipient, message, timestamp, reply) values ('{sender}', '{recipient}', '{message}', '{ctime()}', '{reply}');"
        conn.execute(stmt)

        id = conn.last_insert_rowid()

        result = {"sender":sender, "message":message, "recipients":recipient, "timestamp":ctime(), "reply":reply, "id":id, "error":"no" }
        return result
    except Exception as error:
        result = {"sender":"", "message":"", "recipients":"", "timestamp":"", "reply":"", "error":str(error)}
        return result


@app.route("/logout")
@login_required
def logout():
    stmt = f"UPDATE users SET isActive = 0 WHERE username = '{current_user.id}';"
    conn.execute(stmt)
    stmt = f"INSERT INTO sessions  (username, log, timestamp) values ('{current_user.id}', 0, '{ctime()}');"
    conn.execute(stmt)
    logout_user()
    return flask.redirect('login')


@app.route('/blockUser', methods=['POST','GET'])
def blockUser():
    try:
        username = current_user.id
        usernameBlocked = request.args.get('usernameBlocked') 

        usercheck = f"SELECT username FROM users WHERE username = '{usernameBlocked}';"
        c = conn.execute(usercheck)
        rowsuserCheck = c.fetchall()

        if (username == usernameBlocked) :
                    raise Exception (f'ERROR: You cannot block yourself')
        
        if len(rowsuserCheck) == 0:
                    raise Exception (f'ERROR: {usernameBlocked} is not registered')

        alreadyBlocked = f"SELECT * FROM blocking WHERE (username = '{username}' AND usernameBlocked = '{usernameBlocked}');"
        c = conn.execute(alreadyBlocked)
        rowsalreadyBlocked = c.fetchall()

        if len(rowsalreadyBlocked) > 0:
                    raise Exception (f'ERROR: {usernameBlocked} already blocked')
        
        stmt = f"INSERT INTO blocking (username, usernameBlocked) values ('{username}', '{usernameBlocked}');"
        conn.execute(stmt)

        result = {"username":username, "usernameBlocked":usernameBlocked, "error":"no"}
        return result
    except Exception as error:
        return {"error":str(error)}


@app.route('/unblockUser', methods=['POST','GET'])
def unblockUser():
    username = current_user.id
    usernameBlocked = request.args.get('usernameBlocked')
    stmt = f"DELETE FROM blocking WHERE (username = '{username}' AND usernameBlocked = '{usernameBlocked}');"
    conn.execute(stmt)
    result = {"username":username, "usernameBlocked":usernameBlocked}
    return result

@app.get('/usersBlocked')
def usersBlocked():
    username = current_user.id
    stmt = f"SELECT usernameBlocked FROM blocking WHERE username = '{username}'"
    try:
        c = conn.execute(stmt)
        rows = c.fetchall()
        result = []
        for row in rows:
            result.append({"user" :escape(row[0])})
        return result
    except Error as e:
        return (f'{result}ERROR: {e}', 500)