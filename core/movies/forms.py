from django.contrib.auth.forms import UserCreationForm
from movies.models import MyUser

class MyUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MyUser