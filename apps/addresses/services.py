from .models import Address

class AddressService:
    @staticmethod
    def create_address(user, data):
        return Address.objects.create(user=user, **data)

    @staticmethod
    def update_address(address, data):
        for field, value in data.items():
            setattr(address, field, value)
        address.save()
        return address

    @staticmethod
    def delete_address(address):
        address.delete()
        return True
