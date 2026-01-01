1. Fix problematic payment logic.
    Files:
     - billing.py | create_customer()
     - customers/models.py | save()
    Problem:
       Currently there is a problem with the fact, that save() isnt transactional. It should be kept default, 
       and the logic moved elsewhere. So a dedicated function responsible for creating a stripe_id, that 
       decides on what to do with various errors that may occur.
2. Set up correctly vendor_pull.
    Files:
     - tooling/vendor_pull.py
    Problem:
       Currently its used in docker. I also would likely change flowbite for something else. So likely code 
       for reference.