import ast
import time
from django.http import HttpResponse, Http404, HttpResponseRedirect
from .models import User
import gspread
from gspread import oauth
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow

SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

CREDENTIALS = ast.literal_eval(os.environ.get('CREDENTIALS'))

def delete_one(request, dre):
    try:

        email = request.session['email']
        user = User.objects.filter(email=email)
        authorized_user = ast.literal_eval(user[0].user_key)

        gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

        sh = gc.open('Medicina 259')
        worksheet = sh.sheet1

        column_values = worksheet.col_values(1)
        row_index = column_values.index(dre) + 1

        worksheet.delete_row(row_index)

        dre_sh = gc.open(dre)
        gc.del_spreadsheet(dre_sh.id)

        return HttpResponse("Removido com sucesso.")

    except:
        raise Http404("Houve um erro.")


def send_one(request, dre):
    try:

        email = request.session['email']
        user = User.objects.filter(email=email)
        authorized_user = ast.literal_eval(user[0].user_key)

        gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

        sh = gc.open('Medicina 259')
        worksheet = sh.sheet1
        column_values = worksheet.col_values(1)
        row = column_values.index(dre) + 1
        email = worksheet.row_values(row)[2]

        dre_sh = gc.open(dre)
        dre_sh.share(email_address=email, perm_type='user', role='reader', notify=True,
                     email_message="Notas atualizadas.")

        return HttpResponse("Adicionado com enviado!")

    except:
        raise Http404("Houve um erro.")


def create(request):
    try:

        email = request.session['email']
        user = User.objects.filter(email=email)
        authorized_user = ast.literal_eval(user[0].user_key)

        gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

        sh = gc.open("Medicina 259")
        worksheet = sh.sheet1
        list_rows = worksheet.get_all_values()
        header = list_rows[0]

        time.sleep(5)

        for i, row in enumerate(list_rows):
            dre = row[0].strip()
            if i == 0 or dre == "":
                pass
            else:
                name = row[1].strip()
                email = row[2].strip()

                row_index = i + 1
                my_range = "A" + str(row_index) + ":C" + str(row_index)
                worksheet.batch_update([{
                    'range': my_range,
                    'values': [[dre, name, email]],
                }])

                try:
                    new_sh = gc.open(dre)
                    new_worksheet = new_sh.sheet1
                    new_worksheet.clear()
                    new_worksheet.insert_rows([header, row], row=1)
                except gspread.exceptions.SpreadsheetNotFound:
                    gc.create(dre)
                    new_sh = gc.open(dre)
                    new_worksheet = new_sh.sheet1
                    new_worksheet.update_title("Notas " + dre)
                    new_worksheet.insert_rows([header, row], row=1)

        return HttpResponse("Planilhas criadas com sucesso!")
    except:
        raise Http404("Um erro aconteceu. Tente novamente!")


def send(request):

    email = request.session['email']
    user = User.objects.filter(email=email)
    authorized_user = ast.literal_eval(user[0].user_key)

    gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

    sh = gc.open('Medicina 259')
    worksheet = sh.sheet1
    list_rows = worksheet.get_all_values()

    for i, row in enumerate(list_rows):
        dre = row[0]
        email_student = row[2]

        if dre == "" or i == 0:
            pass
        else:
            new_sh = gc.open(dre)

            new_sh.share(
                email_student, perm_type='user', role='reader', notify=True, email_message="Notas atualizadas."
            )

            time.sleep(5)

    return HttpResponse("Envio realizado com sucesso!")


def delete(request):

    email = request.session['email']
    user = User.objects.filter(email=email)

    authorized_user = ast.literal_eval(user[0].user_key)

    gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

    sh = gc.open('Medicina 259')
    worksheet = sh.sheet1
    list_rows = worksheet.get_all_values()

    for i, row in enumerate(list_rows):
        dre = row[0]
        if i == 0 or dre == "":
            pass
        else:
            id_sh = gc.open(dre).id
            gc.del_spreadsheet(id_sh)

            time.sleep(5)

    return HttpResponse("Remoção realizada com sucesso!")


def oauth_redirect(request):

    email = request.GET.get('email')
    request.session['email'] = email

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CREDENTIALS,
        scopes=SCOPES
    )

    flow.redirect_uri = '/callback'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    request.session['state'] = state

    return HttpResponseRedirect(authorization_url)


def oauth_callback(request):
    state = request.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CREDENTIALS,
        scopes=SCOPES,
        state=state
    )

    flow.redirect_uri = 'callback'

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    user_key = ast.literal_eval(flow.credentials)

    request.session['user_key'] = user_key

    try:
        email = request.session['email']
        user = User.objects.filter(email=email)

        if user:
            user[0].user_key = user_key
            user[0].save()

        else:
            new_user = User(email=email, user_key=user_key)
            new_user.save()

        return HttpResponse("Login Efetuado.")

    except:
        raise Http404("Ocorreu um erro.")

