def enhance_request(request):
    request.data["created_by"] = request.user.id
    request.data["updated_by"] = request.user.id
    return request
