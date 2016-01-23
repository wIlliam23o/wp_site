# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import apps.timekeeper.models
import django.db.models.deletion
from django.conf import settings
import datetime
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TKAddress',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('disabled', models.BooleanField(help_text='Whether this address is disabled (not viewable/included).', default=False)),
                ('number', models.IntegerField(help_text='House number for the address.', blank=True, default=0)),
                ('street', models.CharField(help_text='Street name for the address.', blank=True, default='', max_length=150)),
                ('city', models.CharField(help_text='City name for the address.', blank=True, default='jasper', max_length=150)),
                ('state', models.CharField(help_text='State abbreviation for the address.', blank=True, default='al', max_length=2)),
            ],
            options={
                'verbose_name_plural': 'addresses',
                'verbose_name': 'address',
                'db_table': 'timekeeper_address',
            },
        ),
        migrations.CreateModel(
            name='TKConfig',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('start_work_day', models.CharField(help_text='Starting day for the work week.', default='friday', choices=[('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')], verbose_name='work week start day', max_length=9)),
                ('work_day_hours', models.FloatField(help_text='Number of hours in a work day.', default=8.0, verbose_name='work day hours')),
            ],
            options={
                'verbose_name': 'timekeeper config',
            },
        ),
        migrations.CreateModel(
            name='TKEmployee',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('disabled', models.BooleanField(help_text='Whether this employee is disabled (not viewable/included).', default=False)),
                ('first_name', models.CharField(help_text='First name for the employee.', max_length=25)),
                ('last_name', models.CharField(help_text='Last name for the employee.', max_length=25)),
                ('wage_currency', djmoney.models.fields.CurrencyField(default='USD', choices=[('AFN', 'Afghani'), ('DZD', 'Algerian Dinar'), ('ARS', 'Argentine Peso'), ('AMD', 'Armenian Dram'), ('AWG', 'Aruban Guilder'), ('AUD', 'Australian Dollar'), ('AZN', 'Azerbaijanian Manat'), ('BSD', 'Bahamian Dollar'), ('BHD', 'Bahraini Dinar'), ('THB', 'Baht'), ('BBD', 'Barbados Dollar'), ('BYR', 'Belarussian Ruble'), ('BZD', 'Belize Dollar'), ('BMD', 'Bermudian Dollar (customarily known as Bermuda Dollar)'), ('BTN', 'Bhutanese ngultrum'), ('VEF', 'Bolivar Fuerte'), ('XBA', 'Bond Markets Units European Composite Unit (EURCO)'), ('BRL', 'Brazilian Real'), ('BND', 'Brunei Dollar'), ('BGN', 'Bulgarian Lev'), ('BIF', 'Burundi Franc'), ('XOF', 'CFA Franc BCEAO'), ('XAF', 'CFA franc BEAC'), ('XPF', 'CFP Franc'), ('CAD', 'Canadian Dollar'), ('CVE', 'Cape Verde Escudo'), ('KYD', 'Cayman Islands Dollar'), ('CLP', 'Chilean peso'), ('XTS', 'Codes specifically reserved for testing purposes'), ('COP', 'Colombian peso'), ('KMF', 'Comoro Franc'), ('CDF', 'Congolese franc'), ('BAM', 'Convertible Marks'), ('NIO', 'Cordoba Oro'), ('CRC', 'Costa Rican Colon'), ('HRK', 'Croatian Kuna'), ('CUP', 'Cuban Peso'), ('CUC', 'Cuban convertible peso'), ('CZK', 'Czech Koruna'), ('GMD', 'Dalasi'), ('DKK', 'Danish Krone'), ('MKD', 'Denar'), ('DJF', 'Djibouti Franc'), ('STD', 'Dobra'), ('DOP', 'Dominican Peso'), ('VND', 'Dong'), ('XCD', 'East Caribbean Dollar'), ('EGP', 'Egyptian Pound'), ('ETB', 'Ethiopian Birr'), ('EUR', 'Euro'), ('XBB', 'European Monetary Unit (E.M.U.-6)'), ('XBD', 'European Unit of Account 17(E.U.A.-17)'), ('XBC', 'European Unit of Account 9(E.U.A.-9)'), ('FKP', 'Falkland Islands Pound'), ('FJD', 'Fiji Dollar'), ('HUF', 'Forint'), ('GHS', 'Ghana Cedi'), ('GIP', 'Gibraltar Pound'), ('XAU', 'Gold'), ('XFO', 'Gold-Franc'), ('PYG', 'Guarani'), ('GNF', 'Guinea Franc'), ('GYD', 'Guyana Dollar'), ('HTG', 'Haitian gourde'), ('HKD', 'Hong Kong Dollar'), ('UAH', 'Hryvnia'), ('ISK', 'Iceland Krona'), ('INR', 'Indian Rupee'), ('IRR', 'Iranian Rial'), ('IQD', 'Iraqi Dinar'), ('IMP', 'Isle of Man pount'), ('JMD', 'Jamaican Dollar'), ('JOD', 'Jordanian Dinar'), ('KES', 'Kenyan Shilling'), ('PGK', 'Kina'), ('LAK', 'Kip'), ('KWD', 'Kuwaiti Dinar'), ('AOA', 'Kwanza'), ('MMK', 'Kyat'), ('GEL', 'Lari'), ('LVL', 'Latvian Lats'), ('LBP', 'Lebanese Pound'), ('ALL', 'Lek'), ('HNL', 'Lempira'), ('SLL', 'Leone'), ('LSL', 'Lesotho loti'), ('LRD', 'Liberian Dollar'), ('LYD', 'Libyan Dinar'), ('SZL', 'Lilangeni'), ('LTL', 'Lithuanian Litas'), ('MGA', 'Malagasy Ariary'), ('MWK', 'Malawian Kwacha'), ('MYR', 'Malaysian Ringgit'), ('TMM', 'Manat'), ('MUR', 'Mauritius Rupee'), ('MZN', 'Metical'), ('MXN', 'Mexican peso'), ('MDL', 'Moldovan Leu'), ('MAD', 'Moroccan Dirham'), ('NGN', 'Naira'), ('ERN', 'Nakfa'), ('NAD', 'Namibian Dollar'), ('NPR', 'Nepalese Rupee'), ('ANG', 'Netherlands Antillian Guilder'), ('ILS', 'New Israeli Sheqel'), ('RON', 'New Leu'), ('TWD', 'New Taiwan Dollar'), ('NZD', 'New Zealand Dollar'), ('KPW', 'North Korean Won'), ('NOK', 'Norwegian Krone'), ('PEN', 'Nuevo Sol'), ('MRO', 'Ouguiya'), ('TOP', 'Paanga'), ('PKR', 'Pakistan Rupee'), ('XPD', 'Palladium'), ('MOP', 'Pataca'), ('PHP', 'Philippine Peso'), ('XPT', 'Platinum'), ('GBP', 'Pound Sterling'), ('BWP', 'Pula'), ('QAR', 'Qatari Rial'), ('GTQ', 'Quetzal'), ('ZAR', 'Rand'), ('OMR', 'Rial Omani'), ('KHR', 'Riel'), ('MVR', 'Rufiyaa'), ('IDR', 'Rupiah'), ('RUB', 'Russian Ruble'), ('RWF', 'Rwanda Franc'), ('XDR', 'SDR'), ('SHP', 'Saint Helena Pound'), ('SAR', 'Saudi Riyal'), ('RSD', 'Serbian Dinar'), ('SCR', 'Seychelles Rupee'), ('XAG', 'Silver'), ('SGD', 'Singapore Dollar'), ('SBD', 'Solomon Islands Dollar'), ('KGS', 'Som'), ('SOS', 'Somali Shilling'), ('TJS', 'Somoni'), ('LKR', 'Sri Lanka Rupee'), ('SDG', 'Sudanese Pound'), ('SRD', 'Surinam Dollar'), ('SEK', 'Swedish Krona'), ('CHF', 'Swiss Franc'), ('SYP', 'Syrian Pound'), ('BDT', 'Taka'), ('WST', 'Tala'), ('TZS', 'Tanzanian Shilling'), ('KZT', 'Tenge'), ('TTD', 'Trinidad and Tobago Dollar'), ('MNT', 'Tugrik'), ('TND', 'Tunisian Dinar'), ('TRY', 'Turkish Lira'), ('TVD', 'Tuvalu dollar'), ('AED', 'UAE Dirham'), ('XFU', 'UIC-Franc'), ('USD', 'US Dollar'), ('UGX', 'Uganda Shilling'), ('UYU', 'Uruguayan peso'), ('UZS', 'Uzbekistan Sum'), ('VUV', 'Vatu'), ('KRW', 'Won'), ('YER', 'Yemeni Rial'), ('JPY', 'Yen'), ('CNY', 'Yuan Renminbi'), ('ZMK', 'Zambian Kwacha'), ('ZMW', 'Zambian Kwacha'), ('ZWD', 'Zimbabwe Dollar A/06'), ('ZWN', 'Zimbabwe dollar A/08'), ('ZWL', 'Zimbabwe dollar A/09'), ('PLN', 'Zloty')], editable=False, max_length=3)),
                ('wage', djmoney.models.fields.MoneyField(help_text='Hourly wage for the employee.', max_digits=4, default=Decimal('0.0'), default_currency='USD', decimal_places=2)),
                ('user', models.OneToOneField(related_name='employee', related_query_name='employees', blank=True, to=settings.AUTH_USER_MODEL, null=True, help_text='Welborn Prod. user for this employee.', default=None, on_delete=django.db.models.deletion.SET_DEFAULT)),
            ],
            options={
                'verbose_name_plural': 'employees',
                'verbose_name': 'employee',
                'db_table': 'timekeeper_employee',
            },
        ),
        migrations.CreateModel(
            name='TKJob',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('disabled', models.BooleanField(help_text='Whether this job is disabled (not viewable/included).', default=False)),
                ('name', models.CharField(help_text='A unique name for the job.', max_length=255)),
                ('paid', models.BooleanField(help_text='Whether this job has been paid for.', default=False)),
                ('notes', models.TextField(help_text='Notes pertaining to this job (html is okay).', blank=True, default='', max_length=1024)),
                ('address', models.ForeignKey(blank=True, related_name='jobs', related_query_name='job', help_text='Address for the job.', to='timekeeper.TKAddress', default=1, verbose_name='address', on_delete=django.db.models.deletion.SET_DEFAULT)),
            ],
            options={
                'verbose_name_plural': 'jobs',
                'verbose_name': 'job',
                'db_table': 'timekeeper_job',
            },
        ),
        migrations.CreateModel(
            name='TKSession',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('disabled', models.BooleanField(help_text='Whether this session is disabled (not viewable/included).', default=False)),
                ('start_time', models.DateTimeField(help_text='Start time for the session.', default=datetime.datetime.now)),
                ('stop_time', models.DateTimeField(help_text='Stop time for the session.', default=apps.timekeeper.models.now_plus)),
                ('paid', models.BooleanField(help_text='Whether this session has been paid for.', default=False)),
                ('employees', models.ManyToManyField(help_text='Employees for this session.', related_query_name='employee', to='timekeeper.TKEmployee', related_name='employees', verbose_name='employees')),
                ('job', models.ForeignKey(related_name='sessions', related_query_name='session', help_text='Job for this session.', to='timekeeper.TKJob', verbose_name='job')),
            ],
            options={
                'verbose_name_plural': 'sessions',
                'ordering': ['-start_time'],
                'verbose_name': 'session',
                'db_table': 'timekeeper_session',
            },
        ),
        migrations.CreateModel(
            name='TKZipCode',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('disabled', models.BooleanField(help_text='Whether this zipcode is disabled (not viewable/included).', default=False)),
                ('code', models.CharField(blank=True, default='35501', max_length=5)),
                ('code2', models.CharField(blank=True, default='', max_length=5)),
            ],
            options={
                'verbose_name_plural': 'zipcodes',
                'verbose_name': 'zipcode',
                'db_table': 'timekeeper_zipcode',
            },
        ),
        migrations.AddField(
            model_name='tkaddress',
            name='zipcode',
            field=models.ForeignKey(blank=True, related_name='addresses', related_query_name='address', help_text='ZipCode for the address.', to='timekeeper.TKZipCode', default=1, verbose_name='zipcode', on_delete=django.db.models.deletion.SET_DEFAULT),
        ),
    ]
