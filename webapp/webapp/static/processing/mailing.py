import smtplib

def send_procompet_to_user(dest_email):
    email = 'procompet.prometheus@rore.group'

    server = smtplib.SMTP('relay.roregroup.net', 25)
    server.ehlo() #  стандарт протокола
    #server.starttls()
    #server.login(email, password)

    #dest_email = 'anastasiya.oselskaya@rore.group'
    subject = 'Prometheus procompet'
    email_text = 'Results'
    message = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (email, dest_email, subject, email_text)

    server.set_debuglevel(1) # Необязательно; так будут отображаться данные с сервера в консоли
    server.sendmail(email, dest_email, message)
    server.quit()



def send_celeb_detection_to_user(dest_email):
    email = 'celebdetection.prometheus@rore.group'

    server = smtplib.SMTP('relay.roregroup.net', 25)
    server.ehlo() #  стандарт протокола
    #server.starttls()
    #server.login(email, password)

    #dest_email = 'anastasiya.oselskaya@rore.group'
    subject = 'Celebrities detection'
    email_text = 'Results'
    message = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (email, dest_email, subject, email_text)

    server.set_debuglevel(1) # Необязательно; так будут отображаться данные с сервера в консоли
    server.sendmail(email, dest_email, message)
    server.quit()


def send_to_ai(dest_email):
    email = 'ai.prometheus@rore.group'

    server = smtplib.SMTP('relay.roregroup.net', 25)
    server.ehlo() #  стандарт протокола
    #server.starttls()
    #server.login(email, password)

    #dest_email = 'anastasiya.oselskaya@rore.group'
    subject = 'Prometheus test'
    email_text = 'Results for AI'
    message = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (email, dest_email, subject, email_text)

    server.set_debuglevel(1) # Необязательно; так будут отображаться данные с сервера в консоли
    server.sendmail(email, dest_email, message)
    server.quit()