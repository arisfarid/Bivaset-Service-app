import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ProposalForm from './ProposalForm';

const ProjectList = ({ role }) => {
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await axios.get('http://185.204.171.107:8000/api/projects/');
        setProjects(response.data);
      } catch (error) {
        console.error('خطا در بارگذاری پروژه‌ها:', error);
      }
    };
    fetchProjects();
  }, []);

  return (
    <div>
      <h3>لیست پروژه‌ها</h3>
      {projects.map(project => (
        <div key={project.id} className="project-item">
          <p><strong>عنوان:</strong> {project.title}</p>
          <p><strong>دسته:</strong> {project.category}</p>
          <p><strong>محل:</strong> {project.service_location === 'client_site' ? 'محل کارفرما' : project.service_location === 'contractor_site' ? 'محل مجری' : 'غیرحضوری'}</p>
          {project.location && <p><strong>موقعیت:</strong> {project.location}</p>}
          <p><strong>بودجه:</strong> {project.budget ? project.budget + ' تومان' : 'مشخص نشده'}</p>
          <p><strong>توضیحات:</strong> {project.description || 'ندارد'}</p>
          <p><strong>وضعیت:</strong> {project.status === 'open' ? 'باز' : 'تکمیل‌شده'}</p>
          {role === 'contractor' && project.status === 'open' && <ProposalForm projectId={project.id} />}
        </div>
      ))}
    </div>
  );
};

export default ProjectList;
