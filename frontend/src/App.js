import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import ProjectList from './components/ProjectList';
import ProposalForm from './components/ProposalForm';
import './index.css';

const Register = () => {
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState('client');

  const handleRegister = async () => {
    try {
      await axios.post('http://185.204.171.107:8000/api/users/', { phone, role });
      alert('ثبت‌نام با موفقیت انجام شد!');
    } catch (error) {
      alert('خطا در ثبت‌نام: ' + (error.response?.data?.error || 'مشکل ناشناخته'));
    }
  };

  return (
    <div className="container">
      <h2>ثبت‌نام</h2>
      <input type="text" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="شماره تلفن" />
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="client">کارفرما</option>
        <option value="contractor">مجری</option>
      </select>
      <button onClick={handleRegister}>ثبت‌نام</button>
    </div>
  );
};

const ProjectForm = () => {
  const [category, setCategory] = useState('');
  const [serviceLocation, setServiceLocation] = useState('client_site');
  const [location, setLocation] = useState('');
  const [budget, setBudget] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async () => {
    try {
      await axios.post('http://185.204.171.107:8000/api/projects/', {
        user: 1,
        category,
        service_location: serviceLocation,
        location: serviceLocation === 'client_site' ? location : '',
        budget: budget || null,
        description,
        title: category ? `${category} - ${serviceLocation}` : 'پروژه بدون عنوان', // اضافه کردن title
      });
      alert('پروژه ثبت شد!');
    } catch (error) {
      alert('خطا در ثبت پروژه!' + (error.response?.data?.detail || ''));
    }
  };

  return (
    <div className="container">
      <h2>ثبت پروژه</h2>
      <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="دسته خدمات" />
      <select value={serviceLocation} onChange={(e) => setServiceLocation(e.target.value)}>
        <option value="client_site">محل کارفرما</option>
        <option value="contractor_site">محل مجری</option>
        <option value="remote">غیرحضوری</option>
      </select>
      {serviceLocation === 'client_site' && (
        <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="موقعیت" />
      )}
      <input value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="بودجه (تومان)" type="number" />
      <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="توضیحات" />
      <button onClick={handleSubmit}>ثبت</button>
    </div>
  );
};

const ClientPanel = () => (
  <div className="container">
    <h2>پنل کارفرما</h2>
    <ProjectList role="client" />
  </div>
);

const ContractorPanel = () => (
  <div className="container">
    <h2>پنل مجری</h2>
    <ProjectList role="contractor" />
  </div>
);

const App = () => {
  return (
    <Router>
      <nav>
        <Link to="/register">ثبت‌نام</Link> | <Link to="/project">ثبت پروژه</Link> | 
        <Link to="/client">پنل کارفرما</Link> | <Link to="/contractor">پنل مجری</Link>
      </nav>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/project" element={<ProjectForm />} />
        <Route path="/client" element={<ClientPanel />} />
        <Route path="/contractor" element={<ContractorPanel />} />
      </Routes>
    </Router>
  );
};

export default App;