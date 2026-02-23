from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dotacion', '0002_alter_colaborador_options_colaborador_comuna_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='colaborador',
            name='codigo_ficha',
            field=models.IntegerField(null=True, blank=True, verbose_name='Código Ficha'),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='area',
            field=models.CharField(max_length=150, null=True, blank=True, verbose_name='Área'),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='seccion',
            field=models.CharField(max_length=150, null=True, blank=True, verbose_name='Sección'),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='estado_civil',
            field=models.CharField(max_length=50, null=True, blank=True, verbose_name='Estado Civil'),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='tipo_contrato',
            field=models.CharField(max_length=50, null=True, blank=True, verbose_name='Tipo Contrato'),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='turno',
            field=models.CharField(max_length=200, null=True, blank=True, verbose_name='Turno'),
        ),
        migrations.AddField(
            model_name='colaborador',
            name='estado_ficha',
            field=models.CharField(max_length=50, null=True, blank=True, default='Vigente', verbose_name='Estado Ficha'),
        ),
    ]