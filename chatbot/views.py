from django.shortcuts import render,redirect,get_list_or_404, get_object_or_404
from django.http import JsonResponse
from  openai import OpenAI
import os
from dotenv import load_dotenv
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Chat
from django.utils import timezone
from django.views.decorators.cache import cache_control
import backoff
import openai


load_dotenv()
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))


app_name = 'chatbot'

@backoff.on_exception(backoff.expo, openai.RateLimitError)
def ask_openai_with_backoff(**kwargs):
    return client.chat.completions.create(
        **kwargs
    )



def ask_openai(message):

    # Legacy Completion 
    # response = client.completions.create(
    #     model="gpt-3.5-turbo-instruct",
    #     prompt=message,
    #     max_tokens =150,
    #     n=1,
    #     stop=None,
    #     temperature=0.7,
    # )

    # answer = response.choices[0].text.strip()

    # GPT3.5 Completion
    response = ask_openai_with_backoff(model='gpt-3.5-turbo',
        messages=[
            {"role":"system", "content":"You are an helpful assistant"},
            {"role":"user", "content":message},
    ])

    answer = response.choices[0].message.content.strip()
    return answer

# Create your views here.

# view for chatbot homepage render view
@login_required(login_url='/login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def chatbot(request):
    chat_history = Chat.objects.filter(user = request.user, is_delete =False)


    if request.method =='POST':
        message = request.POST.get('message').strip()
        response = ask_openai(message=message)

        chat = Chat(user=request.user,message=message,response=response,created_at=timezone.now())
        chat.save()
        return JsonResponse({'message':message, 'response': response})
    return render(request, 'chatbot.html',{'chat_history':chat_history})


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(request, username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect('chatbot')
        else:
            error_message='Invalid Username or Password'
            return render(request, 'login.html',{'error_message':error_message})
    else:
        return render(request,'login.html')

def logout(request):
    auth.logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            error_message="Passwords do not match"
            return render(request,'register.html',{'error_message':error_message})
        else:
            try:
                user = User.objects.create_user(username,email,password1)
                user.save()
                auth.login(request,user)
                return redirect('chatbot')

            except:
                error_message = "Error creating account"
                return render(request,'register.html',{'error_message':error_message})
    return render(request,'register.html')


def delete_chat(request):

    # chats = get_list_or_404(Chat, pk=pk)

    if request.method == 'POST':         # If method is POST,
        # Chat.objects.filter(user =  request.user).delete() #Hard Delete
        Chat.objects.filter(user =  request.user,is_delete=False).update(is_delete=True) #Soft Delete
        # chats.delete()                     # delete the cat.
        return redirect('/')             # Finally, redirect to the homepage.

    return render(request, 'chatbot.html')
    # If method is not POST, render the default template.
    




