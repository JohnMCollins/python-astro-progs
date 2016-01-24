      subroutine avevar(data, n, ave, var)

      DOUBLE PRECISION data(n), ave, var

      ave = 0.0
      var = 0.0
      do 11 j=1, n
        ave = ave + data(j)
11    continue
      ave = ave/n

      do 12 j = 1, n
        s = data(j) - ave
        var = var + s*s
12    continue
      var = var / (n-1)
      return
      end

C     Hacked by jmc to use my choice of frequencies

      SUBROUTINE period(x,y,n,px,py,np,jmax,prob)
      INTEGER n,np,NMAX,jmax
      DOUBLE PRECISION prob,px(np),py(np),x(n),y(n)
      PARAMETER (NMAX=5000)
CU    USES avevar
      INTEGER i,j
      DOUBLE PRECISION ave, c, cc, cwtau, pnow, s, ss, sumc, sumcy,sums,
     *sumsh, sumsy, swtau, var, wtau, xave, xmax, xmin, yy, expy, effm
      DOUBLE PRECISION arg,wtemp,wi(NMAX),wpi(NMAX),wpr(NMAX),wr(NMAX),
     *TWOPID
      PARAMETER (TWOPID=6.2831853071795865D0)

      call avevar(y, n, ave, var)
      xmax = x(1)
      xmin = x(1)
      do 11 j=1, n
        if(x(j).gt.xmax) xmax = x(j)
        if(x(j).lt.xmin) xmin = x(j)
11    continue

C          write (*,*) 'VAR=', var

      xave = 0.5 * (xmax + xmin)

      pnow = px(1)

      do 12 j=1, n
        arg = TWOPID * ((x(j)-xave) * pnow)
        wpr(j) =-2.d0 * sin(0.5d0 * arg) ** 2
        wpi(j) = sin(arg)
        wr(j) = cos(arg)
        wi(j) = wpi(j)
12    continue

      do 15 i=1, np
        pnow = px(i)
        sumsh = 0.
        sumc = 0.
        do 13 j= 1, n
          c = wr(j)
          s = wi(j)
          sumsh = sumsh + s * c
          sumc = sumc + (c-s) * (c+s)
13      continue

        wtau = 0.5 * atan2(2. * sumsh, sumc)
        swtau = sin(wtau)
        cwtau = cos(wtau)
        sums = 0.
        sumc = 0.
        sumsy = 0.
        sumcy = 0.

        do 14 j=1, n
          s = wi(j)
          c = wr(j)
          ss = s * cwtau - c * swtau
          cc = c * cwtau + s * swtau
          sums = sums + ss**2
          sumc = sumc + cc**2
          yy = y(j) - ave
          sumsy = sumsy + yy * ss
          sumcy = sumcy + yy * cc
          wtemp=wr(j)
          wr(j)=(wr(j) * wpr(j) - wi(j) * wpi(j)) + wr(j)
          wi(j)=(wi(j) * wpr(j) + wtemp * wpi(j)) + wi(j)
14      continue

        py(i) = 0.5 * (sumcy**2 / sumc + sumsy**2 / sums) / var
        if (py(i).ge.pymax) then
          pymax=py(i)
          jmax=i
        endif

15    continue
      expy=exp(-pymax)
      effm=2.*np/ofac
      prob=effm*expy
      if(prob.gt.0.01)prob=1.-(1.-expy)**effm
      return
      END

C  (C) Copr. 1986-92 Numerical Recipes Software X!.

C  Main program Fortran L-S, JMC Jul 2015

      integer nmax, rmax, dims, cnum, jmax
      parameter (nmax=2000)
      parameter (rmax=1000000)
      parameter (ndcols=8)
      DOUBLE PRECISION TWOPID
      PARAMETER (TWOPID=6.2831853071795865D0)

      DOUBLE PRECISION x(nmax), y(nmax), tn(ndcols)
      DOUBLE PRECISION resxp(rmax), resx(rmax), resy(rmax), startp
      DOUBLE PRECISION stepp, endp, prob
      character*64 infile, outfile, cstartp, cstepp, cendp, ctyp

       dims = iargc()
       if (dims .ne. 6) then
            write(*,*) 'Usage: lombs infile outfile start step end ty'
            call exit(10)
       end if

       call getarg(1, infile)
       call getarg(2, outfile)
       call getarg(3, cstartp)
       call getarg(4, cstepp)
       call getarg(5, cendp)
       call getarg(6, ctyp)
       read (cstartp, *) startp
       read (cstepp, *) stepp
       read (cendp, *) endp

       if (stepp .le. 0.0) then
         write(*,*) 'Invalid step'
         call exit(9)
       end if

       if (startp .ge. endp) then
        write(*,*) 'Start >= End'
        call exit(10)
       end if

       nsteps = (endp+stepp - startp) / stepp
       if (nsteps .ge. rmax) then
        write(*,*) 'Too many periods', nsteps
        call exit (8)
       end if

       do 1 i = 1, nsteps
        resxp(i) = startp
        resx(i) = TWOPID / startp
        startp = startp + stepp
   1   continue

       if (ctyp .eq. 'ew') then
            cnum = 3
       else
        if (ctyp .eq. 'ps') then
            cnum = 5
        else
            if (ctyp .eq. 'pr') then
                cnum = 7
            else
                write(*,*) 'Unknown type expecting ew,ps,pr'
                call exit(11)
            end if
        end if
       end if

       open(17, file=infile)
       open(18, file=outfile)
       dims = 0
       do 10 i=1, nmax
          read(17, *, end=30) tn
          x(i) = tn(2)
          y(i) = tn(cnum)
          dims = dims + 1
10        continue
30     continue

       call period(x, y, dims, resx, resy, nsteps, jmax, prob)

       write(*,*) 'jmax = ', resxp(jmax), '  prob = ', prob

       do 50 i = 1, nsteps
50     write(18, 51) resxp(i), resy(i)
51     format(2E25.16)
       stop
       end
