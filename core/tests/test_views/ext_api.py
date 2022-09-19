import binascii

from djangorestframework_camel_case.util import underscoreize
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from core import fixtures as f, models as m


def get_date_filters(data, field):
    v = data.get(field)
    if v is None:
        return dict()
    return {field: v}


class ExtApiViewSetTests(APITestCase):
    """ExtApiViewSet tests."""

    def setUp(self):
        self.agency = f.create_agency()
        self.recruiter = f.create_recruiter(self.agency)
        self.client.force_login(self.recruiter)

    def test_check_linkedin_candidate_exists(self):
        """Should return candidate id."""
        candidate = f.create_candidate(self.agency)
        candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        candidate.save()

        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': candidate.linkedin_url}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['candidateId'], candidate.id)

    def test_check_linkedin_candidate_exists_in_another_agency(self):
        """Should return no result for current agency."""
        candidate = f.create_candidate(f.create_agency())
        candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        candidate.save()

        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': candidate.linkedin_url}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['candidateId'], None)

    def test_check_linkedin_candidate_not_exists(self):
        """Should return candidate status."""
        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': 'https://www.linkedin.com/in/someslug/'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['candidateId'], None)

    def test_check_linkedin_candidate_invalid_url(self):
        """Should return error if linkedin url is not valid."""
        url = reverse('ext-api-check-linkedin-candidate-exists')
        data = {'linkedinUrl': 'https://www.invalid.com/in/someslug/'}

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_add_linkedin_candidate(self):
        """Should add a candidate."""
        linkedin_url = 'https://www.linkedin.com/in/someslug/'
        website_url = 'https://somecandidate.pw'
        github_url = 'https://github.com/somecandidate'

        url = reverse('ext-api-add-linkedin-candidate')
        data = {
            'name': 'Some Candidate',
            'headline': 'CEO at Ninja Solutions',
            'company': 'Ninja Solutions',
            'city': 'Tokyo',
            'contactInfo': {
                'linkedIn': linkedin_url,
                'twitter': ['https://twitter.com/somecandidate'],
                'email': 'somecandidate@ninjasolutions.com',
                'website': [website_url, github_url],
            },
            'experience': f.LINKEDIN_EXPERIENCE,
            'education': f.LINKEDIN_EDUCATION,
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], 'OK')
        self.assertFalse(response.json()['merge'])

        candidate_id = response.json()['candidateId']

        candidate = m.Candidate.objects.get(id=candidate_id)
        linkedin_data = candidate.linkedin_data_set.first()

        self.assertEqual(linkedin_data.id, response.json()['dataId'])

        self.assertEqual(linkedin_data.data, underscoreize(data))
        self.assertEqual(linkedin_data.created_by, self.recruiter)

        candidate_data = {
            'organization': candidate.organization,
            'linkedin_url': candidate.linkedin_url,
            'first_name': candidate.first_name,
            'last_name': candidate.last_name,
            'current_position': candidate.current_position,
            'current_company': candidate.current_company,
            'current_city': candidate.current_city,
            'email': candidate.email,
            'website_url': candidate.website_url,
            'github_url': candidate.github_url,
        }

        expected_candidate_data = {
            'organization': self.agency,
            'linkedin_url': linkedin_url,
            'first_name': 'Some',
            'last_name': 'Candidate',
            'current_position': data['headline'],
            'current_company': data['company'],
            'current_city': data['city'],
            'email': data['contactInfo']['email'],
            'website_url': website_url,
            'github_url': github_url,
        }

        for data in f.LINKEDIN_EDUCATION:
            self.assertEqual(
                len(
                    candidate.education_details.filter(
                        institute=data['school'],
                        department=data.get('fos', ''),
                        degree=data.get('degree', ''),
                        currently_pursuing=data.get('currently_pursuing', False),
                        **get_date_filters(data, 'date_start'),
                        **get_date_filters(data, 'date_end'),
                    )
                ),
                1,
                msg=f'Education details not found\n{data}',
            )

        for data in f.LINKEDIN_EXPERIENCE:
            self.assertEqual(
                len(
                    candidate.experience_details.filter(
                        occupation=data.get('title'),
                        company=data.get('org', ''),
                        summary=data.get('desc', ''),
                        currently_pursuing=data.get('currently_pursuing', False),
                        **get_date_filters(data, 'date_start'),
                        **get_date_filters(data, 'date_end'),
                    )
                ),
                1,
                msg=f'Experience details not found\n{data}',
            )

        self.assertDictEqual(candidate_data, expected_candidate_data)

    def test_add_linkedin_candidate_already_exists_in_another_agency(self):
        """Should create a candidate."""
        candidate = f.create_candidate(f.create_agency())
        candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        candidate.save()

        url = reverse('ext-api-add-linkedin-candidate')
        data = {
            'name': 'Some Candidate',
            'headline': 'CEO at Ninja Solutions',
            'company': 'Ninja Solutions',
            'city': 'Tokyo',
            'contactInfo': {'linkedIn': 'https://www.linkedin.com/in/someslug/',},
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], 'OK')

        candidate_id = response.json().get('candidateId')
        self.assertNotEqual(candidate_id, candidate.id)

        created_candidate = m.Candidate.objects.get(id=candidate_id)

        linkedin_data = created_candidate.linkedin_data_set.first()

        self.assertEqual(linkedin_data.data, underscoreize(data))
        self.assertEqual(linkedin_data.created_by, self.recruiter)

    def test_add_linkedin_candidate_already_exists(self):
        """Should add data to a candidate."""
        candidate = f.create_candidate(self.agency)
        candidate.linkedin_url = 'https://www.linkedin.com/in/someslug/'
        candidate.save()

        url = reverse('ext-api-add-linkedin-candidate')
        data = {
            'name': 'Some Candidate',
            'headline': 'CEO at Ninja Solutions',
            'company': 'Ninja Solutions',
            'city': 'Tokyo',
            'contactInfo': {'linkedIn': 'https://www.linkedin.com/in/someslug/',},
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result'], 'OK')

        candidate_id = response.json().get('candidateId')
        self.assertEqual(candidate_id, candidate.id)

        linkedin_data = candidate.linkedin_data_set.first()

        self.assertEqual(linkedin_data.data, underscoreize(data))
        self.assertEqual(linkedin_data.created_by, self.recruiter)

    def test_add_linkedin_candidate_merge(self):
        """Should return merge = True."""
        url = reverse('ext-api-add-linkedin-candidate')
        data = {
            'name': 'Some Candidate',
            'headline': 'CEO at Ninja Solutions',
            'company': 'Ninja Solutions',
            'city': 'Tokyo',
            'contactInfo': {'linkedIn': 'https://www.linkedin.com/in/someslug/',},
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['merge'])

        data['name'] = 'John Smith'
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['merge'])

    def test_add_linkedin_candidate_photo(self):
        """Should add a candidate."""
        image_data = f.get_jpeg_image_content()
        image_base64_data = (
            binascii.b2a_base64(image_data).decode('ascii').replace('\n', '')
        )

        url = reverse('ext-api-add-linkedin-candidate')
        data = {
            'name': 'Some Candidate',
            'headline': 'CEO at Ninja Solutions',
            'company': 'Ninja Solutions',
            'city': 'Tokyo',
            'contactInfo': {'linkedIn': 'https://www.linkedin.com/in/someslug/',},
            'photo_base64': 'data:image/jpeg;base64,' + image_base64_data,
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 200)
        candidate_id = response.json()['candidateId']

        candidate = m.Candidate.objects.get(id=candidate_id)
        self.assertTrue(candidate.photo)
        self.assertEqual(candidate.photo.read(), image_data)

    def test_add_linkedin_candidate_invalid_url(self):
        """Should return error if contactInfo -> linkedIn url is not valid."""
        url = reverse('ext-api-add-linkedin-candidate')
        data = {
            'name': 'Some Candidate',
            'contactInfo': {'linkedIn': 'https://www.invalid.com/in/someslug/',},
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
