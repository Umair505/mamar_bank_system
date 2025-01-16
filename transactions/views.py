from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, ListView
from transactions.models import Transaction
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Sum
from django.views import View
from django.shortcuts import redirect
from django.views.generic import FormView
from .forms import TransferForm
from .models import Transfer
from accounts.models import UserBankAccount
from bankrupt_app.models import IsBankrupt
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
)
from transactions.constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID
from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string

def send_transaction_email(user,amount,subject,template):    
    message = render_to_string(template,{
        'user' : user,
        'amount':amount,
    })
    send_email = EmailMultiAlternatives(subject,message,to=[user.email])
    send_email.attach_alternative(message,"text/html")
    send_email.send()

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })

        return context



class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount 
        account.save(
            update_fields=[
                'balance'
            ]
        )

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )
        send_transaction_email(self.request.user,amount,"Deposit Message","transactions/deposit_email.html")
        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        
        bankrupt_status = IsBankrupt.objects.first()
        if bankrupt_status and bankrupt_status.is_bankrupt:
            messages.error(self.request,'The bank is bankrupt.Withdrawal are disabled')
            return redirect('withdraw_money')
        

        if amount > self.request.user.account.balance:
            messages.error(self.request, 'Insufficient funds.')
            return redirect('withdraw_money')
        
        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )
        send_transaction_email(self.request.user,amount,"Withdrawal Message","transactions/withdraw_email.html")

        return super().form_valid(form)
    
    
    

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account,transaction_type=3,loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )
        send_transaction_email(self.request.user,amount,"Loan Request Confirmation","transactions/loan_request_email.html")
        return super().form_valid(form)
    
    
    
    
class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0 
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })

        return context
    
           
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(
            self.request,
            f'Loan amount is greater than available balance'
        )
        send_transaction_email(self.request.user, loan.amount, "Loan payed Message", "transactions/loan_paid_email.html")
        return redirect('loan_list')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=3)
        print(queryset)
        return queryset
    


class TransferMoneyView(LoginRequiredMixin, FormView):
    template_name = 'transactions/transfer_form.html'
    form_class = TransferForm
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        sender_account = self.request.user.account  
        receiver_account_no = form.cleaned_data['receiver_account_no']
        amount = form.cleaned_data['amount']
        
        try:
            receiver_account = UserBankAccount.objects.get(account_no=receiver_account_no)
        except UserBankAccount.DoesNotExist:
            form.add_error('receiver_account_no', 'Receiver account does not exist.')
            return self.form_invalid(form)
        
        if sender_account.balance < amount:
            form.add_error(None, 'Insufficient balance. Transfer failed.')  # Corrected to add error to form without specifying a field
            return self.form_invalid(form)
        
        sender_account.balance -= amount
        receiver_account.balance += amount
        sender_account.save()
        receiver_account.save()

        Transfer.objects.create(sender=sender_account, receiver=receiver_account, amount=amount)


        # Email to the sender
        sender_email_subject = 'Transfer Successful'
        sender_email_message = render_to_string('transactions/transfer_email_sender.html',{
            'amount': amount,
            'sender_account_no': sender_account.account_no,
            'receiver_account_no': receiver_account_no, 
            'current_balance': sender_account.balance,
        })
        send_sender_email = EmailMultiAlternatives(sender_email_subject, '', to=[self.request.user.email])
        send_sender_email.attach_alternative(sender_email_message, "text/html")
        send_sender_email.send()
        
        
        # Email to the receiver
        receiver_email_subject = 'You Received a Transfer'
        receiver_email_message = render_to_string('transactions/transfer_email_receiver.html',{
            'amount': amount,
            'sender_account_no': sender_account.account_no,
            'receiver_account_no': receiver_account_no, 
            'current_balance': receiver_account.balance,
        })
        send_receiver_email = EmailMultiAlternatives(receiver_email_subject, '', to=[receiver_account.user.email])
        send_receiver_email.attach_alternative(receiver_email_message, "text/html")
        send_receiver_email.send()
        
        messages.success(self.request, f'Successfully transferred ${amount} to Account No: {receiver_account_no}.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error with your transfer. Please correct the errors below.')
        return super().form_invalid(form)
    
    
    
    
    

