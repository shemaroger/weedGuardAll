from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, fullname, password=None, **extra_fields):
        """
        Create and return a regular user with an email, firstname, lastname, and password.
        
        :param email: User's email address
        :param firstname: User's first name
        :param lastname: User's last name
        :param password: User's password
        :param extra_fields: Any additional fields to be added to the user
        :raises ValueError: If email, firstname, or lastname is not provided
        """
        if not email:
            raise ValueError('The Email field must be set')
        if not fullname:
            raise ValueError('The Firstname field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, fullname=fullname,**extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, email, fullname, password=None, **extra_fields):
      
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, fullname,password, **extra_fields)

    def get_by_natural_key(self, email):
        """
        Look up a user by their email address.
        
        :param email: User's email address
        :return: User instance associated with the given email
        """
        return self.get(email=email)
