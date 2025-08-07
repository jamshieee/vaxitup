
        function openPopup() {
            document.getElementById('popup').style.display = 'block';
        }

        function closePopup() {
            document.getElementById('popup').style.display = 'none';
        }

        function selectTimeSlot(slot) {
            document.querySelectorAll('.time-slot').forEach(el => el.classList.remove('selected'));
            slot.classList.add('selected');
            document.getElementById('time').value = slot.textContent;
            closePopup();
        }
