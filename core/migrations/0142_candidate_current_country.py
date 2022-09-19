# Generated by Django 2.2.9 on 2020-02-17 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0141_current_salary'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='current_country',
            field=models.CharField(
                blank=True,
                choices=[
                    ('af', 'Afghanistan'),
                    ('al', 'Albania'),
                    ('dz', 'Algeria'),
                    ('ad', 'Andorra'),
                    ('ao', 'Angola'),
                    ('ag', 'Antigua and Barbuda'),
                    ('ar', 'Argentina'),
                    ('am', 'Armenia'),
                    ('au', 'Australia'),
                    ('at', 'Austria'),
                    ('az', 'Azerbaijan'),
                    ('bs', 'Bahamas'),
                    ('bh', 'Bahrain'),
                    ('bd', 'Bangladesh'),
                    ('bb', 'Barbados'),
                    ('by', 'Belarus'),
                    ('be', 'Belgium'),
                    ('bz', 'Belize'),
                    ('bj', 'Benin'),
                    ('bt', 'Bhutan'),
                    ('bo', 'Bolivia (Plurinational State of)'),
                    ('ba', 'Bosnia and Herzegovina'),
                    ('bw', 'Botswana'),
                    ('br', 'Brazil'),
                    ('bn', 'Brunei Darussalam'),
                    ('bg', 'Bulgaria'),
                    ('bf', 'Burkina Faso'),
                    ('bi', 'Burundi'),
                    ('cv', 'Cabo Verde'),
                    ('kh', 'Cambodia'),
                    ('cm', 'Cameroon'),
                    ('ca', 'Canada'),
                    ('cf', 'Central African Republic'),
                    ('td', 'Chad'),
                    ('cl', 'Chile'),
                    ('cn', 'China'),
                    ('co', 'Colombia'),
                    ('km', 'Comoros'),
                    ('cg', 'Congo'),
                    ('cd', 'Congo, Democratic Republic of the'),
                    ('cr', 'Costa Rica'),
                    ('ci', "Côte d'Ivoire"),
                    ('hr', 'Croatia'),
                    ('cu', 'Cuba'),
                    ('cy', 'Cyprus'),
                    ('cz', 'Czechia'),
                    ('dk', 'Denmark'),
                    ('dj', 'Djibouti'),
                    ('dm', 'Dominica'),
                    ('do', 'Dominican Republic'),
                    ('ec', 'Ecuador'),
                    ('eg', 'Egypt'),
                    ('sv', 'El Salvador'),
                    ('gq', 'Equatorial Guinea'),
                    ('er', 'Eritrea'),
                    ('ee', 'Estonia'),
                    ('sz', 'Eswatini'),
                    ('et', 'Ethiopia'),
                    ('fj', 'Fiji'),
                    ('fi', 'Finland'),
                    ('fr', 'France'),
                    ('ga', 'Gabon'),
                    ('gm', 'Gambia'),
                    ('ge', 'Georgia'),
                    ('de', 'Germany'),
                    ('gh', 'Ghana'),
                    ('gr', 'Greece'),
                    ('gd', 'Grenada'),
                    ('gt', 'Guatemala'),
                    ('gn', 'Guinea'),
                    ('gw', 'Guinea-Bissau'),
                    ('gy', 'Guyana'),
                    ('ht', 'Haiti'),
                    ('hn', 'Honduras'),
                    ('hu', 'Hungary'),
                    ('is', 'Iceland'),
                    ('in', 'India'),
                    ('id', 'Indonesia'),
                    ('ir', 'Iran (Islamic Republic of)'),
                    ('iq', 'Iraq'),
                    ('ie', 'Ireland'),
                    ('il', 'Israel'),
                    ('it', 'Italy'),
                    ('jm', 'Jamaica'),
                    ('jp', 'Japan'),
                    ('jo', 'Jordan'),
                    ('kz', 'Kazakhstan'),
                    ('ke', 'Kenya'),
                    ('ki', 'Kiribati'),
                    ('kp', "Korea (Democratic People's Republic of)"),
                    ('kr', 'Korea, Republic of'),
                    ('kw', 'Kuwait'),
                    ('kg', 'Kyrgyzstan'),
                    ('la', "Lao People's Democratic Republic"),
                    ('lv', 'Latvia'),
                    ('lb', 'Lebanon'),
                    ('ls', 'Lesotho'),
                    ('lr', 'Liberia'),
                    ('ly', 'Libya'),
                    ('li', 'Liechtenstein'),
                    ('lt', 'Lithuania'),
                    ('lu', 'Luxembourg'),
                    ('mg', 'Madagascar'),
                    ('mw', 'Malawi'),
                    ('my', 'Malaysia'),
                    ('mv', 'Maldives'),
                    ('ml', 'Mali'),
                    ('mt', 'Malta'),
                    ('mh', 'Marshall Islands'),
                    ('mr', 'Mauritania'),
                    ('mu', 'Mauritius'),
                    ('mx', 'Mexico'),
                    ('fm', 'Micronesia (Federated States of)'),
                    ('md', 'Moldova, Republic of'),
                    ('mc', 'Monaco'),
                    ('mn', 'Mongolia'),
                    ('me', 'Montenegro'),
                    ('ma', 'Morocco'),
                    ('mz', 'Mozambique'),
                    ('mm', 'Myanmar'),
                    ('na', 'Namibia'),
                    ('nr', 'Nauru'),
                    ('np', 'Nepal'),
                    ('nl', 'Netherlands'),
                    ('nz', 'New Zealand'),
                    ('ni', 'Nicaragua'),
                    ('ne', 'Niger'),
                    ('ng', 'Nigeria'),
                    ('mk', 'North Macedonia'),
                    ('no', 'Norway'),
                    ('om', 'Oman'),
                    ('pk', 'Pakistan'),
                    ('pw', 'Palau'),
                    ('pa', 'Panama'),
                    ('pg', 'Papua New Guinea'),
                    ('py', 'Paraguay'),
                    ('pe', 'Peru'),
                    ('ph', 'Philippines'),
                    ('pl', 'Poland'),
                    ('pt', 'Portugal'),
                    ('qa', 'Qatar'),
                    ('ro', 'Romania'),
                    ('ru', 'Russian Federation'),
                    ('rw', 'Rwanda'),
                    ('kn', 'Saint Kitts and Nevis'),
                    ('lc', 'Saint Lucia'),
                    ('vc', 'Saint Vincent and the Grenadines'),
                    ('ws', 'Samoa'),
                    ('sm', 'San Marino'),
                    ('st', 'Sao Tome and Principe'),
                    ('sa', 'Saudi Arabia'),
                    ('sn', 'Senegal'),
                    ('rs', 'Serbia'),
                    ('sc', 'Seychelles'),
                    ('sl', 'Sierra Leone'),
                    ('sg', 'Singapore'),
                    ('sk', 'Slovakia'),
                    ('si', 'Slovenia'),
                    ('sb', 'Solomon Islands'),
                    ('so', 'Somalia'),
                    ('za', 'South Africa'),
                    ('ss', 'South Sudan'),
                    ('es', 'Spain'),
                    ('lk', 'Sri Lanka'),
                    ('sd', 'Sudan'),
                    ('sr', 'Suriname'),
                    ('se', 'Sweden'),
                    ('ch', 'Switzerland'),
                    ('sy', 'Syrian Arab Republic'),
                    ('tj', 'Tajikistan'),
                    ('tz', 'Tanzania, United Republic of'),
                    ('th', 'Thailand'),
                    ('tl', 'Timor-Leste'),
                    ('tg', 'Togo'),
                    ('to', 'Tonga'),
                    ('tt', 'Trinidad and Tobago'),
                    ('tn', 'Tunisia'),
                    ('tr', 'Turkey'),
                    ('tm', 'Turkmenistan'),
                    ('tv', 'Tuvalu'),
                    ('ug', 'Uganda'),
                    ('ua', 'Ukraine'),
                    ('ae', 'United Arab Emirates'),
                    ('gb', 'United Kingdom of Great Britain and Northern Ireland'),
                    ('us', 'United States of America'),
                    ('uy', 'Uruguay'),
                    ('uz', 'Uzbekistan'),
                    ('vu', 'Vanuatu'),
                    ('ve', 'Venezuela (Bolivarian Republic of)'),
                    ('vn', 'Viet Nam'),
                    ('ye', 'Yemen'),
                    ('zm', 'Zambia'),
                    ('zw', 'Zimbabwe'),
                ],
                max_length=128,
            ),
        ),
    ]
