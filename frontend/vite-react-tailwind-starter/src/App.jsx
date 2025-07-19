import React, { useState } from 'react';

function App() {
  const [resume, setResume] = useState(null);
  const [coverLetter, setCoverLetter] = useState('');

  const handleResumeChange = (e) => {
    setResume(e.target.files[0]);
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append("resume", resume);

    const response = await fetch("http://localhost:8000/upload-resume", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    alert("Resume uploaded!");
  };

  const generateCoverLetter = async () => {
    const response = await fetch("http://localhost:8000/generate-cover-letter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_title: "Software Engineer" }),
    });

    const data = await response.json();
    setCoverLetter(data.cover_letter);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8 space-y-6">
      <h1 className="text-2xl font-bold">🔥 Job Automation Tool</h1>

      <input
        type="file"
        onChange={handleResumeChange}
        className="text-black"
      />
      <button
        onClick={handleSubmit}
        className="bg-blue-600 px-4 py-2 rounded hover:bg-blue-800"
      >
        Upload Resume
      </button>

      <button
        onClick={generateCoverLetter}
        className="bg-green-600 px-4 py-2 rounded hover:bg-green-800 ml-4"
      >
        Generate Cover Letter
      </button>

      <pre className="mt-4 bg-gray-800 p-4 rounded">
        {coverLetter}
      </pre>
    </div>
  );
}

export default App;
