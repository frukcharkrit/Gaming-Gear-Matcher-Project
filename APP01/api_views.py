# Association Rules API Views
from APP01.association_rules import get_gear_recommendations, refresh_association_rules
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
# from .views import is_admin  <-- Circular import risk

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or (user.role and user.role.role_name == 'Admin'))

import json


@require_http_methods(["POST"])
@login_required
def api_gear_recommendations(request):
    """
    API endpoint to get gear recommendations based on selected gears.
    
    POST data:
        gear_ids: List of gear IDs already selected
        top_n: Number of recommendations (default 5)
        exclude_types: List of gear types to exclude (optional)
    
    Returns:
        JSON with recommended gears and their confidence scores
    """
    try:
        data = json.loads(request.body)
        gear_ids = data.get('gear_ids', [])
        top_n = data.get('top_n', 5)
        exclude_types = data.get('exclude_types', [])
        
        if not gear_ids:
            return JsonResponse({'error': 'No gear IDs provided'}, status=400)
        
        # Get recommendations
        recommendations = get_gear_recommendations(gear_ids, top_n, exclude_types)
        
        # Format response
        results = []
        for rec in recommendations:
            gear = rec['gear']
            results.append({
                'gear_id': gear.gear_id,
                'name': gear.name,
                'type': gear.type,
                'brand': gear.brand,
                'price': str(gear.price) if gear.price else None,
                'image_url': gear.image.url if gear.image else None,
                'confidence': round(rec['confidence'] * 100, 1),  # Convert to percentage
                'lift': round(rec['lift'], 2),
                'score': round(rec['score'], 2)
            })
        
        return JsonResponse({
            'success': True,
            'recommendations': results,
            'count': len(results)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
@user_passes_test(is_admin)
def api_refresh_association_rules(request):
    """
    Admin-only endpoint to manually refresh association rules cache.
    
    Triggers recalculation of association rules from current preset data.
    """
    try:
        success = refresh_association_rules()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Association rules refreshed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to refresh rules - insufficient data'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
