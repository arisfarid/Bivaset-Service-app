import React, { useState } from 'react';
import axios from 'axios';

const ProposalForm = ({ projectId }) => {
  const [price, setPrice] = useState('');
  const [time, setTime] = useState('');

  const handleSubmit = async () => {
    try {
      await axios.post('http://185.204.171.107:8000/api/proposals/', {
        project: projectId,
        contractor: 2, // مجری نمونه، باید با ورود واقعی عوض بشه
        price,
        time,
      });
      alert('پیشنهاد ثبت شد!');
    } catch (error) {
      alert('خطا در ثبت پیشنهاد!');
    }
  };

  return (
    <div>
      <h4>ارسال پیشنهاد</h4>
      <input value={price} onChange={(e) => setPrice(e.target.value)} placeholder="قیمت (تومان)" type="number" />
      <input value={time} onChange={(e) => setTime(e.target.value)} placeholder="زمان (مثلاً: 3 روز)" />
      <button onClick={handleSubmit}>ارسال</button>
    </div>
  );
};

export default ProposalForm;
