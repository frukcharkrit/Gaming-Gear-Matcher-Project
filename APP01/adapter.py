from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import render
from APP01.models import AdminLog


class MyAccountAdapter(DefaultAccountAdapter):
    def respond_user_inactive(self, request, user):
        # Fetch ban details from AdminLog
        ban_log = AdminLog.objects.filter(
            target=user.username, 
            action__icontains='Ban'
        ).order_by('-timestamp').first()
        
        ban_date = ban_log.timestamp if ban_log else None
        
        return render(request, 'account/account_inactive.html', {
            'user': user,
            'ban_date': ban_date
        })


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle social authentication errors"""
        pass
