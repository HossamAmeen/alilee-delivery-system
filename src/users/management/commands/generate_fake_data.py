from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from users.models import Driver

fake = Faker()


class Command(BaseCommand):
    help = "Generate fake data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--drivers",
            type=int,
            default=500,
            help="Number of drivers to create (default: 500)",
        )

    def handle(self, *args, **options):
        num_drivers = options["drivers"]

        self.stdout.write("Starting to generate fake data...")

        try:
            with transaction.atomic():
                # Generate Drivers
                self.stdout.write(f"Creating {num_drivers} drivers...")
                for i in range(num_drivers):
                    driver = Driver.objects.create(
                        email=fake.email(),
                        full_name=fake.name(),
                        balance=fake.random_number(digits=5),
                        phone_number=fake.numerify("010########"),
                        vehicle_number=fake.bothify("???###"),  # Random vehicle number
                        license_number=fake.bothify(
                            "DL####????"
                        ),  # Random license number
                        is_active=True,
                    )
                    # Set a password for the driver
                    driver.set_password("password123")
                    driver.save()

                    if (i + 1) % 50 == 0:
                        self.stdout.write(f"Created {i + 1} drivers...")

                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created {num_drivers} drivers")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {str(e)}"))
            raise e
