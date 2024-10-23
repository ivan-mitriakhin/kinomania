from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from movies.models import Movie, Recommend, Rating
from movies.tasks import csr_append_task, csr_update_task

@receiver(post_save, sender=User)
def create_recommend(sender, instance, created, **kwargs):
    if created:
        r = Recommend(user=instance,
                      recommender_type=instance.RecommenderType.NON_PERSONALIZED)
        r.save()

@receiver(post_save, sender=User)
def X_append_row(sender, instance, created, **kwargs):
    if created:
        csr_append_task.delay_on_commit(axis=0)

@receiver(post_save, sender=Movie)
def X_append_col(sender, instance, created, **kwargs):
    if created:
        csr_append_task.delay_on_commit(axis=1)

@receiver(post_save, sender=Rating)
def X_insert_value(sender, instance, created, **kwargs):
    csr_update_task.delay_on_commit(
        instance.owner.pk, 
        instance.movie.pk,
        instance.value,
        save=True
    )

@receiver(post_delete, sender=Rating)
def X_delete_value(sender, instance, **kwargs):
    csr_update_task.delay_on_commit(
        instance.owner.pk, 
        instance.movie.pk,
        instance.value,
        save=False
    )