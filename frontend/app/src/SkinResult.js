import { useLocation } from 'react-router-dom';
import { useNavigate } from "react-router-dom";
import React, { useState } from 'react';
import Chatbot from './chatbot'; 


import './SkinResult.css';

const TriangleGraph = ({ probabilities }) => {
  const labels = {
    normal: "보통",
    dry: "건성",
    oily: "지성"
  };

  const categoryLabels = {
    'psoriasis': '건선',
    'pigmentation': '색소침착',
    'acne': '여드름'
  };


  const normalizeValue = (value) => {
    return 0.2 + (value / 100) * 0.6;
  };

  const getPolygonPoints = (scale = 1) => {
    const radius = 60 * scale;
    return [
      `${100},${100 - radius}`,
      `${100 + radius * Math.cos(Math.PI / 6)},${100 + radius * Math.sin(Math.PI / 6)}`,
      `${100 - radius * Math.cos(Math.PI / 6)},${100 + radius * Math.sin(Math.PI / 6)}`
    ].join(' ');
  };

  const getDataPoints = () => {
    const normalRadius = 60 * normalizeValue(probabilities.normal);
    const oilyRadius = 60 * normalizeValue(probabilities.oily);
    const dryRadius = 60 * normalizeValue(probabilities.dry);

    return [
      `${100},${100 - normalRadius}`,
      `${100 + oilyRadius * Math.cos(Math.PI / 6)},${100 + oilyRadius * Math.sin(Math.PI / 6)}`,
      `${100 - dryRadius * Math.cos(Math.PI / 6)},${100 + dryRadius * Math.sin(Math.PI / 6)}`
    ].join(' ');
  };

  return (
    <div className="triangle-graph">
      <svg viewBox="0 0 200 200">
        {/* 배경 원 */}
        {[0.8, 0.6, 0.4, 0.2].map((scale, i) => (
          <circle
            key={i}
            cx="100"
            cy="100"
            r={80 * scale}
            fill="none"
            stroke="#7d7d7d"
            strokeWidth="0.5"
            opacity="0.5"
          />
        ))}

        {/* 기준 삼각형들 */}
        {[0.8, 0.6, 0.4, 0.2].map((scale, i) => (
          <polygon
            key={i}
            points={getPolygonPoints(scale)}
            fill="none"
            stroke="#7d7d7d"
            strokeWidth="0.5"
            opacity="0.5"
          />
        ))}

        {/* 데이터 폴리곤 */}
        <polygon
          points={getDataPoints()}
          fill="#5eb3f7"
          fillOpacity="0.3"
          stroke="#2196F3"
          strokeWidth="2"
        />

        {/* 라벨과 값 */}
        <text x="100" y="15" fill="#666" textAnchor="middle" className="label">
          {labels.normal}
        </text>
        <text x="100" y="30" fill="#666" textAnchor="middle" className="value">
          {probabilities.normal}%
        </text>

        <text x="200" y="160" fill="#666" textAnchor="end" className="label">
          {labels.oily}
        </text>
        <text x="200" y="175" fill="#666" textAnchor="end" className="value">
          {probabilities.oily}%
        </text>

        <text x="20" y="160" fill="#666" textAnchor="start" className="label">
          {labels.dry}
        </text>
        <text x="20" y="175" fill="#666" textAnchor="start" className="value">
          {probabilities.dry}%
        </text>
      </svg>
    </div>
  );
};

const SkinResult = () => {
  const location = useLocation();
  const navigate = useNavigate(); 
  const [isOpen, setIsOpen] = useState(false); 
  const { analysisData } = location.state || {};

  const labels = {
    normal: "보통",
    dry: "건성",
    oily: "지성"
  };

  console.log('Location state:', location.state);
  console.log('Analysis data:', location.state?.analysisData);

  const categoryLabels = {
    'psoriasis': '건선',
    'pigmentation': '색소침착',
    'acne': '여드름'
  };

  if (!analysisData) {
    console.log('No analysis data received');
    return null;
  }

  const getImageSrc = (imageData) => {
    if (!imageData) {
      console.log('No image data');
      return null;
    }
    
    try {

      if (imageData.length % 4 !== 0) {
        console.error('Invalid base64 data');
        return null;
      }

      if (imageData.startsWith('data:image')) {
        return imageData;
      }
      

      return `data:image/jpeg;base64,${imageData.replace(/[\n\r]/g, '')}`;
    } catch (error) {
      console.error('Error processing image data:', error);
      return null;
    }
  };

  const defectData  = analysisData.skin_defect_analysis;

  console.log('전체 분석 데이터:', analysisData);
  console.log('결함 데이터:', defectData);
  console.log('이미지 데이터 존재 여부:', !!defectData?.image);
  console.log('이미지 데이터 미리보기:', defectData?.image?.substring(0, 100));
  console.log('예측 데이터:', defectData?.predictions);

  const { 
    file_name, 
    skin_type_analysis, 
    skin_flushing_analysis,
    skin_wrinkle_analysis,
    skin_pores_analysis,
    skin_advice,
    // skin_defect_analysis  
  } = analysisData;

  return (
    <div className="result-container">
      <video className="background-video" autoPlay loop muted>
        <source src={process.env.PUBLIC_URL + "/image/gj.mp4"} type="video/mp4" />
      </video>

      <h1 className="main-title">
        <span style={{ color: '#e7466b' }}>😊</span>
        피부 분석 결과
        <span style={{ color: '#e7466b' }}>😊</span>
      </h1>

      {/* 피부 관리 조언 섹션 */}
      <div className="sections-container">
        <div className="advice-section">
          <h2 className="section-title">ai맞춤 피부 관리 조언</h2>
          <div className="advice-box">
            {skin_advice && skin_advice.advice ? (
              <div className="advice-content">
                {skin_advice.advice}
              </div>
            ) : (
              <div className="advice-loading">
                피부 분석 결과를 바탕으로 맞춤형 조언을 생성하고 있습니다.
              </div>
            )}
          </div>
        </div>
        
        {/* 3개 카드를 감싸는 컨테이너 */}
        <div className="cards-row">
          {/* 피부 타입 카드 */}
          <div className="result-card">
            <h2 className="card-title">피부 타입</h2>
            <div className="card-content">
              <div className="info-row">
                <span className="label">업로드한 사진: </span>
                <span className="value">{file_name}</span>
              </div>
              <div className="info-row">
                <span className="label">주요 타입:</span>
                <span className="value highlight">
                  {labels[skin_type_analysis?.prediction] || skin_type_analysis?.prediction}
                </span>
              </div>
              
              {skin_type_analysis?.probabilities && (
                <div className="triangle-container">
                  <TriangleGraph probabilities={skin_type_analysis.probabilities} />
                </div>
              )}
            </div>
          </div>

          {/* 피부 상태 카드 */}
          <div className="result-card">
            <h2 className="card-title">피부 상태</h2>
            <div className="card-content">
              <div className="status-item">
                <div className="status-value">
                  {skin_flushing_analysis?.prediction === 'flushing' ? (
                    <span className="status-text positive">✓ 홍조 있음</span>
                  ) : (
                    <span className="status-text negative">✗ 홍조 없음</span>
                  )}
                </div>
              </div>

              <div className="status-item">
                <div className="status-value">
                  {skin_wrinkle_analysis?.prediction === 'wrinkle' ? (
                    <span className="status-text positive">✓ 주름 있음</span>
                  ) : (
                    <span className="status-text negative">✗ 주름 없음</span>
                  )}
                </div>
              </div>

              <div className="status-item">
                <div className="status-value">
                  {skin_pores_analysis?.prediction === 'pores' ? (
                    <span className="status-text positive">✓ 모공 있음</span>
                  ) : (
                    <span className="status-text negative">✗ 모공 없음</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 피부 결함 카드 */}
          <div className="result-card">
            <h2 className="card-title">피부 결함</h2>
            <div className="card-content">
              {defectData?.predictions && defectData.predictions.length > 0 ? (
                <div className="defect-content">
                  {defectData.image && (
                    <div className="result-image-container">
                      <img 
                        src={getImageSrc(defectData.image)}
                        alt="결함 분석 결과" 
                        className="result-image"
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="no-defect">
                  <span className="negative">✗ 감지된 피부 결함 없음</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <Chatbot />
    </div>
  );
};

export default SkinResult;