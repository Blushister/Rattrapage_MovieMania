from django import forms
from django.test import TestCase
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    """Form for user login validation"""
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={
            'placeholder': 'email@domain.com',
            'class': 'form-input',
            'required': True
        })
    )
    password = forms.CharField(
        min_length=6,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe',
            'class': 'form-input', 
            'required': True
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return email.lower().strip()
        return email


class RegisterForm(forms.Form):
    """Form for user registration validation"""
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={
            'placeholder': 'email@domain.com',
            'class': 'form-input',
            'required': True
        })
    )
    password = forms.CharField(
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe (min 8 caractères)',
            'class': 'form-input',
            'required': True
        })
    )
    genres = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    def __init__(self, genres_choices=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if genres_choices:
            self.fields['genres'].choices = genres_choices

    def clean_genres(self):
        genres = self.cleaned_data.get('genres')
        if not genres or len(genres) < 3:
            raise ValidationError('Please select at least 3 genres.')
        return genres

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            # Check for at least one number
            if not any(char.isdigit() for char in password):
                raise ValidationError('Password must contain at least one number.')
            # Check for at least one letter
            if not any(char.isalpha() for char in password):
                raise ValidationError('Password must contain at least one letter.')
        return password


class ProfileForm(forms.Form):
    """Form for user profile update validation"""
    GENDER_CHOICES = [
        ('', 'Non spécifié'),
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('O', 'Autre')
    ]

    nom = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nom de famille',
            'class': 'form-input'
        })
    )
    prenom = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Prénom',
            'class': 'form-input'
        })
    )
    birthday = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input'
        })
    )
    sexe = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    def clean_birthday(self):
        birthday = self.cleaned_data.get('birthday')
        if birthday:
            from datetime import date
            today = date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            if age < 13:
                raise ValidationError('You must be at least 13 years old.')
            if age > 120:
                raise ValidationError('Please enter a valid birth date.')
        return birthday


class PasswordChangeForm(forms.Form):
    """Form for password change validation"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mot de passe actuel',
            'class': 'form-input',
            'required': True
        })
    )
    new_password = forms.CharField(
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Nouveau mot de passe',
            'class': 'form-input',
            'required': True
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirmer le nouveau mot de passe',
            'class': 'form-input',
            'required': True
        })
    )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        if password:
            # Check for at least one number
            if not any(char.isdigit() for char in password):
                raise ValidationError('Password must contain at least one number.')
            # Check for at least one letter
            if not any(char.isalpha() for char in password):
                raise ValidationError('Password must contain at least one letter.')
        return password

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('The two password fields must match.')
        
        return confirm_password


class RatingForm(forms.Form):
    """Form for movie rating validation"""
    movie_id = forms.IntegerField(min_value=1)
    rating = forms.IntegerField(min_value=1, max_value=5)

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise ValidationError('Rating must be between 1 and 5.')
        return rating


# Test Cases
class LoginFormTestCase(TestCase):
    def test_valid_login_form(self):
        """Test valid login form"""
        form_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')

    def test_invalid_email_format(self):
        """Test invalid email format"""
        form_data = {
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_short_password(self):
        """Test password too short"""
        form_data = {
            'email': 'test@example.com',
            'password': '12345'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_email_normalization(self):
        """Test email is normalized to lowercase"""
        form_data = {
            'email': 'TEST@EXAMPLE.COM',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')


class RegisterFormTestCase(TestCase):
    def setUp(self):
        self.genres_choices = [
            ('1', 'Action'),
            ('2', 'Comedy'),
            ('3', 'Drama'),
            ('4', 'Horror'),
            ('5', 'Romance')
        ]

    def test_valid_registration_form(self):
        """Test valid registration form"""
        form_data = {
            'email': 'newuser@example.com',
            'password': 'validpass123',
            'genres': ['1', '2', '3']
        }
        form = RegisterForm(genres_choices=self.genres_choices, data=form_data)
        self.assertTrue(form.is_valid())

    def test_insufficient_genres(self):
        """Test insufficient genre selection"""
        form_data = {
            'email': 'newuser@example.com',
            'password': 'validpass123',
            'genres': ['1', '2']  # Only 2 genres
        }
        form = RegisterForm(genres_choices=self.genres_choices, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('genres', form.errors)

    def test_password_without_number(self):
        """Test password without number"""
        form_data = {
            'email': 'newuser@example.com',
            'password': 'validpassword',
            'genres': ['1', '2', '3']
        }
        form = RegisterForm(genres_choices=self.genres_choices, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_password_without_letter(self):
        """Test password without letter"""
        form_data = {
            'email': 'newuser@example.com',
            'password': '12345678',
            'genres': ['1', '2', '3']
        }
        form = RegisterForm(genres_choices=self.genres_choices, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_short_password(self):
        """Test password too short"""
        form_data = {
            'email': 'newuser@example.com',
            'password': 'test123',  # 7 characters, need 8
            'genres': ['1', '2', '3']
        }
        form = RegisterForm(genres_choices=self.genres_choices, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)


class ProfileFormTestCase(TestCase):
    def test_valid_profile_form(self):
        """Test valid profile form"""
        form_data = {
            'nom': 'Doe',
            'prenom': 'John',
            'birthday': '1990-01-01',
            'sexe': 'M'
        }
        form = ProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_profile_form(self):
        """Test empty profile form (all fields optional)"""
        form_data = {}
        form = ProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_too_young_birthday(self):
        """Test birthday that makes user too young"""
        from datetime import date, timedelta
        recent_date = date.today() - timedelta(days=365*10)  # 10 years old
        
        form_data = {
            'birthday': recent_date.strftime('%Y-%m-%d')
        }
        form = ProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('birthday', form.errors)

    def test_unrealistic_birthday(self):
        """Test unrealistic old birthday"""
        form_data = {
            'birthday': '1800-01-01'
        }
        form = ProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('birthday', form.errors)


class PasswordChangeFormTestCase(TestCase):
    def test_valid_password_change(self):
        """Test valid password change form"""
        form_data = {
            'current_password': 'oldpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        form = PasswordChangeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Test password confirmation mismatch"""
        form_data = {
            'current_password': 'oldpass123',
            'new_password': 'newpass123',
            'confirm_password': 'different123'
        }
        form = PasswordChangeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_weak_new_password(self):
        """Test weak new password"""
        form_data = {
            'current_password': 'oldpass123',
            'new_password': 'weakpass',
            'confirm_password': 'weakpass'
        }
        form = PasswordChangeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('new_password', form.errors)


class RatingFormTestCase(TestCase):
    def test_valid_rating(self):
        """Test valid rating form"""
        form_data = {
            'movie_id': 123,
            'rating': 4
        }
        form = RatingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_rating_too_low(self):
        """Test rating too low"""
        form_data = {
            'movie_id': 123,
            'rating': 0
        }
        form = RatingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_invalid_rating_too_high(self):
        """Test rating too high"""
        form_data = {
            'movie_id': 123,
            'rating': 6
        }
        form = RatingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_invalid_movie_id(self):
        """Test invalid movie ID"""
        form_data = {
            'movie_id': 0,
            'rating': 4
        }
        form = RatingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('movie_id', form.errors)