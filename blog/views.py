from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator, InvalidPage
from django.db.models import Q
from .models import *
from .forms import *
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

class Custom_Paginator:
    def __init__(self, request, queryset, paginated_by):
        self.paginator = Paginator(queryset, paginated_by)
        self.paginated_by = paginated_by
        self.queryset = queryset
        self.page = request.GET.get('page', 1)
        
    def get_queryset(self):
        try:
            queryset = self.paginator.page(self.page)
        except PageNotAnInteger:
            queryset = self.paginator.page(1)
        except EmptyPage:
            queryset = self.paginator.page(1)
        except InvalidPage:
            queryset = self.paginator.page(1)
        
        return queryset
    
    

class Home(generic.TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                
                'blogs': Blog.objects.order_by('-created_date'),
                'tags': Tag.objects.order_by('-created_date'),
                
            }
        )
        
        context['current_path'] = self.request.path
        
        return context


class All_Blogs(generic.ListView):
    model = Blog
    template_name = 'all_blogs.html'
    context_object_name = 'blogs'
    paginate_by = 4
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = Tag.objects.order_by('-created_date')
        page_obj = Custom_Paginator(self.request, self.get_queryset(), self.paginate_by)
        queryset = page_obj.get_queryset()
        paginator = page_obj.paginator
        context['blogs'] = queryset
        context['paginator'] = paginator
        context['tags'] = tags
        context['current_path'] = self.request.path
        
        return context


class Blog_details(generic.DetailView):
    model = Blog
    template_name = 'blog_details.html'
    context_object_name = 'B'
    slug_url_kwarg = 'slug'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = Tag.objects.order_by('-created_date')
        
        context['related_blogs'] = self.get_object().related
        context['tags'] = tags
        context['form'] = TextForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Get the blog object based on the slug
        blog = self.get_object()
        form = TextForm(request.POST)
        
        if request.method == "POST" and request.user.is_authenticated:
            if form.is_valid():
                
                comment = form.cleaned_data.get('text')
                Review.objects.create(
                    user=request.user,
                    blog=blog,
                    comment=comment,
                    
                )
                # Redirect back to the blog details page
                return redirect('blog_details', slug=blog.slug)
        
        # If the form is not valid or the user is not authenticated, render the page again with errors
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class Category_details(generic.DetailView):
    model = Category
    template_name = 'category_details.html'
    slug_url_kwarg = 'slug'
    paginate_by = 4
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recent_blogs = Blog.objects.order_by('-created_date')
        tags = Tag.objects.order_by('-created_date')
        
        category = self.get_object()
        category_products = category.category_blogs.all()
        
        page_obj = Custom_Paginator(self.request, category_products, self.paginate_by)
        queryset = page_obj.get_queryset()
        
        context['blogs'] = queryset
        context['paginator'] = page_obj.paginator
        context['page_obj'] = queryset
        context['is_paginated'] = queryset.has_other_pages()
        context['tags'] = tags
        context['recent_blogs'] = recent_blogs
        context['category_products'] = category_products
        
        return context
    
    
class Tag_details(generic.DetailView):
    model = Tag
    template_name = 'tag_details.html'
    slug_url_kwarg = 'slug'
    paginate_by = 4
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recent_blogs = Blog.objects.order_by('-created_date')
        tags = Tag.objects.order_by('-created_date')
        
        tag = self.get_object()
        tag_blogs = tag.tag_blogs.all()
        
        page_obj = Custom_Paginator(self.request, tag_blogs, self.paginate_by)
        queryset = page_obj.get_queryset()
        
        context['blogs'] = queryset
        context['paginator'] = page_obj.paginator
        context['page_obj'] = queryset
        context['is_paginated'] = queryset.has_other_pages()
        context['tags'] = tags
        context['recent_blogs'] = recent_blogs
        context['tag_blogs'] = tag_blogs
        
        return context


class Search_Blogs(generic.View):
    
    def get(self, *args, **kwargs):
        key = self.request.GET.get('key', '')
        
        recent_blogs = Blog.objects.order_by('-created_date')
        tags = Tag.objects.order_by('-created_date')
        
        blog = Blog.objects.filter(
            Q(title__icontains=key) |
            Q(category__title__icontains=key) |
            Q(user__username__icontains=key) |
            Q(tags__title__icontains=key)
        )

        context = {
            'blogs': blog,
            'key': key,
            'recent_blogs': recent_blogs,
            'tags': tags
        }

        return render(self.request, 'search_blogs.html', context)



class AddBlog(LoginRequiredMixin, generic.CreateView):
    model = Blog
    form_class = AddBlogForm
    template_name = 'add_blog.html'
    login_url = 'login'

    def form_valid(self, form):
        # Handle tags and the user/category assignment
        tags = self.request.POST.get('tags').split(',')
        user = get_object_or_404(User, pk=self.request.user.pk)
        category = get_object_or_404(Category, pk=self.request.POST.get('category'))
        
        blog = form.save(commit=False)
        blog.user = user
        blog.category = category
        blog.save()

        for tag in tags:
            tag_input = Tag.objects.filter(
                title__iexact=tag.strip(),
                slug=slugify(tag.strip())
            )
            if tag_input.exists():
                t = tag_input.first()
                blog.tags.add(t)
            else:
                if tag != '':
                    new_tag = Tag.objects.create(
                        title=tag.strip(),
                        slug=slugify(tag.strip())
                    )
                    blog.tags.add(new_tag)

        messages.success(self.request, "Blog added successfully")
        return super().form_valid(form)


    def get_success_url(self):
        # Redirect to the blog details page after successful submission
        return reverse_lazy('blog_details', kwargs={'slug': self.object.slug})
    


class MyBlogs(LoginRequiredMixin, generic.ListView):
    model = Blog
    template_name = 'my_blogs.html'
    paginate_by = 6
    login_url = 'login'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        userblog = self.request.user.user_blogs.all()
        page_obj = Custom_Paginator(self.request, userblog, self.paginate_by)
        queryset = page_obj.get_queryset()

        context['blogs'] = queryset
        context['paginator'] = page_obj.paginator
        context['page_obj'] = queryset
        context['is_paginated'] = queryset.has_other_pages()
        
        return context

    def dispatch(self, request, *args, **kwargs):
        delete = request.GET.get('delete', None)

        if delete:
            blog = get_object_or_404(Blog, pk=delete)

            if request.user.pk != blog.user.pk:
                return redirect('home')

            blog.delete()
            messages.success(request, "Your blog has been deleted!")
            return redirect('my_blogs')

        return super().dispatch(request, *args, **kwargs)
    


def add_favourite(request, id):
    blog = get_object_or_404(Blog, id=id)

    if request.user.is_authenticated:
        # Using Favorite model (for separate favorites list)
        if blog.favourite.filter(id=request.user.id).exists():
            # Already favorited, so do nothing (or display a message)
            pass
        else:
            blog.favourite.add(request.user)
            messages.success(request, "Blog added to favourite list") 
    else:
        # User not authenticated, consider redirecting to login
        messages.warning(request, "Please login to add favourite!!") 
        return redirect('login')

    return redirect('blog_details', slug=blog.slug)



class Favourite_list(LoginRequiredMixin, generic.ListView):
    model = Blog
    template_name = 'favourite.html'
    paginate_by = 6
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        favourite_blogs = self.request.user.favourite_blogs.all()
        page_obj = Custom_Paginator(self.request, favourite_blogs, self.paginate_by)
        queryset = page_obj.get_queryset()

        context['blogs'] = queryset
        context['paginator'] = page_obj.paginator
        context['page_obj'] = queryset
        context['is_paginated'] = queryset.has_other_pages()
        
        return context
    

    def dispatch(self, request, *args, **kwargs):
        delete = request.GET.get('delete', None)

        if delete:
            blog = get_object_or_404(Blog, pk=delete)

            # Check if the blog is in the user's favorite blogs
            if blog in request.user.favourite_blogs.all():
                # Remove the blog from the user's favorite list
                request.user.favourite_blogs.remove(blog)
                messages.success(request, "Blog has been removed from your favorites!")
            else:
                messages.error(request, "Blog not found in your favorites!")

            return redirect('favourite_list')

        return super().dispatch(request, *args, **kwargs)



class UpdateBlog(LoginRequiredMixin, generic.UpdateView):
    model = Blog
    form_class = AddBlogForm
    template_name = 'update_blog.html'
    login_url = 'login'
    
    def get_object(self, queryset=None):
        
        slug = self.kwargs.get('slug')
        blog = get_object_or_404(Blog, slug=slug)
        return blog
    
    def form_valid(self, form):
        blog = form.instance  # Get the blog object before saving
        user = self.request.user
        
        # Check if the user owns the blog
        if blog.user != user:
            return redirect('home')
        
        # Handle category
        category = get_object_or_404(Category, pk=self.request.POST['category'])
        blog.category = category
        
        # Save the blog without committing to the database yet
        blog = form.save(commit=False)
        blog.user = user
        blog.save()
        
        # Clear existing tags
        blog.tags.clear()  # Remove all old tags
        
        # Handle tags logic
        tags = self.request.POST['tags'].split(',')
        for tag in tags:
            tag = tag.strip()
            if tag:
                existing_tag = Tag.objects.filter(
                    title__iexact=tag,
                    slug=slugify(tag)
                ).first()
                if existing_tag:
                    blog.tags.add(existing_tag)
                else:
                    new_tag = Tag.objects.create(
                        title=tag,
                        slug=slugify(tag)
                    )
                    blog.tags.add(new_tag)
        
        # Success message and redirect to the blog details page
        messages.success(self.request, "Blog updated successfully")
        return redirect('blog_details', slug=blog.slug)
    


