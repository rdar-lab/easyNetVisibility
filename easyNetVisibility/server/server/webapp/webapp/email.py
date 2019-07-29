from flask_mail import Message

recipient = None
mail = None


def init(param_mail, param_recipient):
    global mail
    global recipient

    mail = param_mail
    recipient = param_recipient


def email_user(subject, body):
    if recipient is not None:
        try:
            msg = Message(subject, recipients=[recipient])
            msg.html = body
            mail.send(msg)
            return "email sent"
        except Exception, e:
            return str(e)
    else:
        return "No email configured"
