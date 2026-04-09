import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../store/authSlice';
import type { RootState } from '../store/store';
import '../styles/header.css';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const user = useSelector((state: RootState) => state.auth.user);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="logo">🚨 FinFlag</h1>
        <nav className="nav">
          <span className="user-info">Welcome, {user?.username}!</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </nav>
      </div>
    </header>
  );
};