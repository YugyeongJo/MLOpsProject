import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './FileUpload.css';
// import SkinResult from './SkinResult';

function FileUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [responseMessage, setResponseMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type.startsWith('image/')) {
        setSelectedFile(file);
      } else {
        alert("이미지 파일만 업로드할 수 있습니다.");
        setSelectedFile(null);
      }
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!selectedFile) {
      alert("파일을 선택해주세요.");
      return;
    }
    
    setLoading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    
    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", { 
        method: "POST",
        body: formData,
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("서버 응답 데이터:", data);  
      setAnalysisData(data);

      // const defectFormData = new FormData();
      // defectFormData.append("file", selectedFile);
      
      // const defectResponse = await fetch("http://localhost:8004/predict", {
      //   method: "POST",
      //   body: defectFormData,
      // });
      
      // const defectData = await defectResponse.json();
      // console.log("Defect 분석 데이터:", defectData);

      if (response.ok) {
        setResponseMessage("분석이 완료되었습니다");
        navigate('/result', { 
          state: {
            analysisData: data
           }
        });
      } else {
        setResponseMessage(`업로드 실패: ${data.message}`);
        alert(`업로드 실패: ${data.message}`);
      }
    } catch (error) {
      console.error("에러:", error);
      alert("업로드 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
};

  return (
    <>
      <div className="upload-guide">
        <h2>😊사진 촬영 전 유의사항😊</h2>
        <ul>
          <li><strong>1. 잘 보이는 조명에서 촬영해주세요. 🌞</strong> 자연광 아래에서 촬영하는 것이 가장 좋습니다. 너무 어두운 곳에서 찍거나, 강한 조명이 직접 비추지 않도록 주의해주세요.</li>
          <li><strong>2. 얼굴이 선명하게 보이도록 해주세요. 😊</strong> 카메라를 얼굴과 약간의 거리 두고, 얼굴이 전체적으로 잘 보이도록 찍어주세요.</li>
          <li><strong>3. 카메라는 정면으로 두고 촬영해주세요. 📸</strong> 얼굴을 정면으로 바라보고, 카메라는 눈높이에 맞추어 얼굴 전체가 잘 보이도록 촬영해주세요.</li>
          <li><strong>4. 메이크업과 스킨케어 제품을 피해주세요. 💄❌</strong> 피부 상태를 정확하게 판별하기 위해 메이크업이나 스킨케어 제품 없이 깨끗한 피부 상태로 사진을 찍어주세요.</li>
          <li><strong>5. 배경을 단순하게 해주세요. 🏞️</strong> 복잡한 배경을 피하고 깔끔하고 밝은 배경에서 찍어주세요.</li>
          <li><strong>6. 사진을 업로드 전에 확인해주세요. 👀</strong> 찍은 사진이 선명하고 얼굴이 잘 보이는지 다시 한번 확인한 후 업로드해 주세요.</li>
        </ul>
      </div>

      <div className="background-video">
        <video autoPlay muted loop className="background-video-element">
          <source src={process.env.PUBLIC_URL + "/image/gj.mp4"} type="video/mp4" />
          해당 브라우저는 동영상을 지원하지 않습니다.
        </video>
      </div>

      {loading && (
        <div className="overlay">
          <div className="spinner">
            <div className="dot1"></div>
            <div className="dot2"></div>
            <div className="dot3"></div>
          </div>
        </div>
      )}

      <div className="file-upload-container">
        <header className="header">
          <h1>Sprout Clinic</h1>
        </header>
        <div className="upload-section">
          <form onSubmit={handleSubmit} className="file-upload-form">
            <label htmlFor="file-input" className="file-label">
              <img
                src={process.env.PUBLIC_URL + "/image/folderandfile_122790.png"}
                // src={process.env.PUBLIC_URL + "/image/file.jpg"}
                alt="파일 업로드"
                className="file-image"
              />
            </label>
            <input
              id="file-input"
              type="file"
              onChange={handleFileChange}
              className="file-input"
              style={{ display: 'none' }} 
            />
            {selectedFile && (
              <div className="image-preview">
                <img
                  src={URL.createObjectURL(selectedFile)} 
                  alt="Selected File"
                  className="image-preview-img"
                />
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="upload-button"
            >
              {loading ? '분석 중...' : '분석하기'}
            </button>
          </form>
        </div>

        {responseMessage && (
          <p className={`response-message ${responseMessage.includes('실패') ? 'error' : 'success'}`}>
            {responseMessage}
          </p>
        )}
      </div>
    </>
  );
}

export default FileUpload;
