from django import forms
from .models import Transaction
from bankrupt_app.models import IsBankrupt
from django import forms
from accounts.models import UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        
        bankrupt_status = IsBankrupt.objects.first()
        if bankrupt_status and bankrupt_status.is_bankrupt:
            raise forms.ValidationError('The bank is bankrupt and cannot process withdraws. ')
        
        
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount}$')

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'you can withdraw at most {max_withdraw_amount}$')
        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} in your account. You can not withdraw more then your account balance')
            
        return amount


class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount
    
class TransferForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, max_digits=12)
    receiver_account_no = forms.IntegerField()

    def clean_receiver_account_no(self):
        receiver_account_no = self.cleaned_data.get('receiver_account_no')
        if not UserBankAccount.objects.filter(account_no=receiver_account_no).exists():
            raise forms.ValidationError('Receiver account does not exist.')
        return receiver_account_no