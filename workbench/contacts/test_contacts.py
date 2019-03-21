from django.test import TestCase

from workbench import factories


def person_to_dict(person, **kwargs):
    return {
        "address": person.address,
        "given_name": person.given_name,
        "family_name": person.family_name,
        "address_on_first_name_terms": person.address_on_first_name_terms,
        "salutation": person.salutation,
        "notes": person.notes,
        "organization": person.organization_id or "",
        "primary_contact": person.primary_contact_id,
        "groups": person.groups.values_list("id", flat=True),
        "is_archived": person.is_archived,
        "phonenumbers-TOTAL_FORMS": 0,
        "phonenumbers-INITIAL_FORMS": 0,
        "phonenumbers-MAX_NUM_FORMS": 1000,
        "emailaddresses-TOTAL_FORMS": 0,
        "emailaddresses-INITIAL_FORMS": 0,
        "emailaddresses-MAX_NUM_FORMS": 1000,
        "postaladdresses-TOTAL_FORMS": 0,
        "postaladdresses-INITIAL_FORMS": 0,
        "postaladdresses-MAX_NUM_FORMS": 1000,
        **kwargs,
    }


class ContactsTest(TestCase):
    def test_update(self):
        person = factories.PersonFactory.create(salutation="Dear")
        self.client.force_login(person.primary_contact)
        response = self.client.post(person.urls["update"], person_to_dict(person))
        self.assertRedirects(response, person.urls["detail"])

    def test_warning(self):
        person = factories.PersonFactory.create(
            organization=factories.OrganizationFactory.create(), salutation="Dear"
        )
        factories.ProjectFactory.create(customer=person.organization, contact=person)

        self.client.force_login(person.primary_contact)
        response = self.client.post(
            person.urls["update"], person_to_dict(person, organization="")
        )
        # print(response, response.content.decode("utf-8"))
        self.assertContains(
            response,
            "Diese Person ist der Kontakt der folgenden zugehörigen Objekte:"
            " 1 Projekt.",
        )
