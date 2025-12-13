## When migrate database, run these commands in shell_plus
### UserAccount.objects.create(email="user@user.com", full_name="user", role=UserRole.OWNER)
### user = UserAccount.objects.get(pk=1)
### user.set_password("password")
### user.save()

## Run orders unit tests
### python manage.py test orders.tests.test_signals_v2 -v 2